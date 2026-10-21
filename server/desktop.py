"""登录用户会话内的连接窗口、托盘和后台服务器。"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import logging
import math
import os
import queue
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from .common import atomic_json
from . import network

LOG = logging.getLogger("desktouch.desktop")
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "DeskTouch"
PRIVATE_NETWORKS = tuple(ipaddress.ip_network(x) for x in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))


def validate_host(host: str) -> str:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("仅允许明确的回环或私有局域网 IPv4 地址，不支持主机名和公网地址。") from exc
    if address.version != 4 or not (address.is_loopback or any(address in network for network in PRIVATE_NETWORKS)):
        raise ValueError("仅允许回环或私有局域网 IPv4 地址；禁止 0.0.0.0、公网及 IPv6 通配绑定。")
    return str(address)


def choose_host(host: str, addresses, preferred=None) -> str | None:
    if host != "lan":
        return validate_host(host)
    from . import network
    rows = network.rank(addresses)
    if preferred:
        for row in rows:
            if row["address"] == preferred:
                return row["address"]
        if not rows:
            return None
        # The saved adapter disappeared; return best remaining so the user keeps a working URL.
        return rows[0]["address"]
    for row in rows:
        try:
            return validate_host(row["address"])
        except ValueError:
            continue
    return None


def validate_test_options(options, data_dir: Path | None = None) -> Path | None:
    ready = options.test_ready_file
    delay = options.test_exit_after
    if ready is None and delay is None:
        return None
    if not options.demo:
        raise ValueError("--test-ready-file 和 --test-exit-after 仅允许 --demo 模式。")
    if options.headless and delay is not None:
        raise ValueError("--test-exit-after 仅适用于桌面，不能与 --headless 一起使用。")
    if not ipaddress.ip_address(validate_host(options.host)).is_loopback:
        raise ValueError("桌面验收开关仅允许回环地址，请显式指定 --host 127.0.0.1。")
    if delay is not None and (not math.isfinite(delay) or delay <= 0):
        raise ValueError("--test-exit-after 必须是有限的正数秒数。")
    if ready is not None and Path(ready).name != "ready.json":
        raise ValueError("验收文件名必须是 ready.json，不能覆盖配置或配对状态文件。")
    if ready is None or data_dir is None:
        return None
    directory, path = Path(data_dir).resolve(), Path(ready).expanduser().resolve()
    if path == directory or not path.is_relative_to(directory) or path.is_dir():
        raise ValueError("验收文件必须是 app.data_dir 内的文件，不能指向目录或目录外。")
    if path.name != "ready.json":
        raise ValueError("验收文件解析后必须仍是 ready.json，不能通过链接覆盖状态文件。")
    return path


def configure_logging(data_dir: Path):
    logs = data_dir / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    path = logs / "desktop.log"
    root = logging.getLogger()
    # 多次调用时只替换本模块自己的文件处理器，不改变其他调用方的日志配置。
    for handler in list(root.handlers):
        if getattr(handler, "_desktouch_desktop", False):
            root.removeHandler(handler)
            handler.close()
    handler = TimedRotatingFileHandler(path, when="midnight", backupCount=7, encoding="utf-8")
    handler._desktouch_desktop = True
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
    return path


def show_error(message: str):
    try:
        from tkinter import messagebox
        messagebox.showerror("DeskTouch", message)
    except Exception:
        LOG.exception("无法显示错误对话框")


def require_user_session():
    if sys.platform != "win32":
        raise RuntimeError("桌面托盘仅支持 Windows；其他环境请使用 --headless。")
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.ProcessIdToSessionId.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    kernel.ProcessIdToSessionId.restype = wintypes.BOOL
    session = wintypes.DWORD()
    if not kernel.ProcessIdToSessionId(os.getpid(), ctypes.byref(session)):
        raise ctypes.WinError(ctypes.get_last_error())
    if session.value == 0:
        raise RuntimeError("DeskTouch 只能在用户登录会话运行，不能作为 Windows 服务启动。")


def current_user_sid() -> str:
    import win32api
    import win32con
    import win32security
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
    try:
        sid = win32security.GetTokenInformation(token, win32security.TokenUser)[0]
        return win32security.ConvertSidToStringSid(sid)
    finally:
        token.Close()


def instance_name(data_dir: Path, user_sid: str) -> str:
    identity = user_sid + "\0" + os.path.normcase(str(data_dir.resolve())).casefold()
    return "Local\\DeskTouch." + hashlib.sha256(identity.encode("utf-8")).hexdigest()


class SingleInstance:
    def __init__(self, data_dir: Path):
        import win32api
        import win32event
        self.api, self.events = win32api, win32event
        self.event = self.mutex = None
        name = instance_name(data_dir, current_user_sid())
        try:
            # 先建事件，避免第二个进程在第一个进程创建事件前丢失唤醒请求。
            self.event = win32event.CreateEvent(None, False, False, name + ".Show")
            self.mutex = win32event.CreateMutex(None, False, name + ".Mutex")
            self.primary = win32api.GetLastError() != 183
            if not self.primary:
                win32event.SetEvent(self.event)
        except BaseException:
            self.close()
            raise

    def consume_show_request(self) -> bool:
        return self.events.WaitForSingleObject(self.event, 0) == self.events.WAIT_OBJECT_0

    def close(self):
        for name in ("mutex", "event"):
            handle = getattr(self, name, None)
            if handle is not None:
                self.api.CloseHandle(handle)
                setattr(self, name, None)


class Autostart:
    def __init__(self, data_dir: Path, *, demo=False, no_autostart=False):
        self.path = data_dir / "desktop.json"
        self.target_dir = data_dir.resolve()
        self.allowed = sys.platform == "win32" and bool(getattr(sys, "frozen", False)) and not demo and not no_autostart
        self.enabled = False
        self.command = ""

    def _matching_selection(self):
        from .storage import stable_data_dir
        location = stable_data_dir().parent / "location.json"
        selection = json.loads(location.read_text(encoding="utf-8")) if location.is_file() else None
        if (isinstance(selection, dict) and isinstance(selection.get("data_dir"), str)
                and selection["data_dir"] and Path(selection["data_dir"]).expanduser().resolve() == self.target_dir):
            return location, selection
        return location, None

    def sync(self, host: str, port: int, data_dir: Path):
        # 测试开关和演示模式甚至不读取注册表，也不改变正式运行的偏好。
        if not self.allowed:
            return
        self.target_dir = data_dir.resolve()
        self.command = subprocess.list2cmdline([
            str(Path(sys.executable).resolve()), "--background", "--host", host,
            "--port", str(port), "--data-dir", str(self.target_dir),
        ])
        location, selection = self._matching_selection()
        preference = {}
        if selection is not None and "autostart" in selection:
            if type(selection["autostart"]) is not bool:
                raise ValueError("location.json 自启偏好无效，请检查日志和该文件。")
            # 已保存的目录选择意图优先，甚至不读取可能过时或损坏的 desktop.json。
            preference = {"autostart": selection["autostart"]}
        elif self.path.exists():
            preference = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(preference, dict) or type(preference.get("autostart")) is not bool:
                raise ValueError("desktop.json 自启偏好无效，请检查日志和该文件。")
        self.enabled = preference.get("autostart", True)
        if selection is not None:
            if "autostart" not in selection:
                selection["autostart"] = self.enabled
                atomic_json(location, selection)
        elif self.target_dir == self.path.parent.resolve() and not self.path.exists():
            atomic_json(self.path, {"autostart": self.enabled})
        # 重定向只更新命令目标，绝不把选择的偏好写回当前目录或写入旧版目录。
        self._apply(self.enabled)

    def _apply(self, enabled: bool):
        import winreg
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, self.command)
            else:
                try:
                    winreg.DeleteValue(key, RUN_VALUE)
                except FileNotFoundError:
                    pass

    def toggle(self):
        if not self.allowed:
            return
        enabled = not self.enabled
        location, selection = self._matching_selection()
        # 先保存用户意图，即使注册表失败，下次启动仍尊重最新选择。
        if selection is not None:
            selection["autostart"] = enabled
            atomic_json(location, selection)
        elif self.target_dir == self.path.parent.resolve():
            atomic_json(self.path, {"autostart": enabled})
        else:
            raise ValueError("目标数据目录选择已改变，请退出后重新启动再修改自启。")
        self.enabled = enabled
        self._apply(enabled)


class BackgroundServer:
    def __init__(self, app, host: str, port: int):
        import uvicorn
        self.config = uvicorn.Config(
            app, host=validate_host(host), port=port, log_config=None, use_colors=False,
            access_log=False, proxy_headers=False, ws_max_size=4096,
            timeout_graceful_shutdown=5,
        )
        self.server = uvicorn.Server(self.config)
        self.error = None
        self.thread = threading.Thread(target=self._run, name="desktouch-server", daemon=True)

    def _run(self):
        listener = None
        try:
            # 先完成绑定再进入 lifespan，端口占用时不会启动应用后台采样。
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if sys.platform == "win32":
                # Windows SO_REUSEADDR 允许占用同一端口；明确要求独占，避免混用其他程序监听。
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            listener.bind((self.config.host, self.config.port))
            listener.listen(self.config.backlog)
            listener.setblocking(False)
            self.server.run(sockets=[listener])
        except BaseException as exc:
            self.error = "服务绑定或启动失败（%s），可能地址不可用或端口已占用。" % exc
            LOG.exception("后台服务器失败")
        finally:
            if listener is not None:
                listener.close()

    def start(self):
        self.thread.start()

    @property
    def alive(self):
        return self.thread.is_alive()

    @property
    def ready(self):
        return self.alive and self.server.started

    def stop(self):
        self.server.should_exit = True
        if self.thread.ident is not None:
            self.thread.join(timeout=15)
            if self.thread.is_alive():
                raise RuntimeError("服务器仍在清理连接，请稍后再次退出；详情见日志。")


class Desktop:
    def __init__(self, options, data_dir: Path, instance: SingleInstance, autostart: Autostart):
        from . import main
        self.options, self.data_dir = options, data_dir
        self.instance, self.autostart = instance, autostart
        validate_test_options(options, data_dir)
        self.app = main.create_app(data_dir=data_dir, demo=options.demo)
        try:
            self.port = options.port if options.port is not None else self.app.state.config.snapshot()["server"]["port"]
            if not 1 <= self.port <= 65535:
                raise ValueError("端口必须在 1–65535 范围内。")
            self.test_ready_file = validate_test_options(options, self.app.state.data_dir)
        except BaseException:
            self._close_modules()
            raise
        self.server = None
        self.host = None
        self.status = "正在启动…"
        self.commands = queue.Queue()
        self.icon = self.root = None
        self.tray_thread = None
        self.quitting = False
        self._reported_server_error = False
        self._last_view = None
        self.pending_data_dir = None
        self._test_ready_written = False
        self._test_ready_failed = False
        self._test_exit_timer = None
        self.address_rows = []
        self.address_map = {}
        self.address_choice = None
        self._address_values = ()
        self._address_note = ""

    @property
    def url(self):
        return "http://%s:%s" % (self.host, self.port) if self.host else ""

    def post(self, action):
        # pystray 回调线程只入队，所有 tkinter 调用均在主线程执行。
        self.commands.put(action)

    def _notify(self, message):
        if self.icon is not None:
            self.icon.title = ("DeskTouch · " + message)[:120]
            try:
                self.icon.notify(message, "DeskTouch")
            except Exception:
                LOG.warning("托盘通知不可用", exc_info=True)

    def start_server(self, *, loopback=False):
        from . import main
        if self.server and self.server.alive:
            self.server.stop()
        if self.server is not None:
            # 绑定失败时 lifespan 尚未运行，也必须关闭构建应用时创建的模块线程。
            self._close_modules()
            # FastAPI lifespan 关闭后其线程池不能复用，重试必须构建新的应用。
            self.app = main.create_app(data_dir=self.data_dir, demo=self.options.demo)
        addresses = main.local_addresses() if self.options.host == "lan" and not loopback else []
        preferred = None
        if self.options.host == "lan" and not loopback:
            preferred = self.app.state.config.snapshot()["server"].get("preferred_host") or None
        self.address_rows = network.candidates() if self.options.host == "lan" and not loopback else []
        self.host = "127.0.0.1" if loopback else choose_host(self.options.host, addresses, preferred)
        if self.host and preferred and self.host != preferred:
            # Saved adapter is gone (Wi-Fi off, dock removed). Fall back but say so.
            self._address_note = "已保存的地址 %s 当前不可用，本次改用 %s。可在下方重新选择。" % (preferred, self.host)
        else:
            self._address_note = ""
        self._reported_server_error = False
        if self.host is None:
            self.server = None
            self.status = "未发现可用的局域网 IPv4（已忽略 WSL/Docker 等虚拟网卡）。连接 Wi-Fi 后重试，或暂用 127.0.0.1（仅本机）。"
            LOG.warning(self.status)
            self._notify(self.status)
            return
        self.status = "正在启动服务：" + self.url
        self.server = BackgroundServer(self.app, self.host, self.port)
        self.server.start()
        self.refresh_view()

    def refresh_code(self):
        self.app.state.auth.rotate()
        self.refresh_view()

    def apply_address_choice(self):
        row = self.address_map.get(self.address_choice.get())
        if not row:
            return
        self.app.state.config.set_preferred_host(row["address"])
        self.options.host = "lan"
        self.start_server()
        self.refresh_view()
        self._notify("连接地址已切换为 " + (self.url or "无可用地址"))

    def show_window(self):
        self.refresh_view()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_window(self):
        self.root.withdraw()

    def open_panel(self):
        if self.server is None or not self.server.ready:
            self.show_window()
            return
        webbrowser.open(self.url)

    def toggle_autostart(self):
        self.autostart.toggle()
        if self.pending_data_dir is not None:
            self._save_directory_selection(self.pending_data_dir)
        if self.icon is not None:
            self.icon.update_menu()
        self.refresh_view()

    def _save_directory_selection(self, directory):
        from .storage import stable_data_dir
        selection = {"data_dir": str(directory)}
        if self.autostart.allowed:
            selection["autostart"] = self.autostart.enabled
        atomic_json(stable_data_dir().parent / "location.json", selection)

    def select_legacy_directory(self):
        from tkinter import filedialog, messagebox
        if self.options.demo:
            messagebox.showinfo("DeskTouch", "演示模式不会修改正式数据目录选择。", parent=self.root)
            return
        if not messagebox.askokcancel(
            "使用旧版数据目录",
            "请选择含 config.json 或 state.json 的旧版 data 目录。\n"
            "不会复制、覆盖或删除原文件，也不会移动其他个人文件。\n"
            "选择将在退出并重新启动 DeskTouch 后生效，届时连接会重新建立。\n"
            "恢复旧配对还需使用平板原来的浏览器和完全相同的地址（协议、IP、端口）。",
            parent=self.root,
        ):
            return
        selected = filedialog.askdirectory(title="选择旧版 DeskTouch 数据目录", parent=self.root, mustexist=True)
        if not selected:
            return
        directory = Path(selected).expanduser().resolve()
        known = [directory / name for name in ("config.json", "state.json")]
        if not directory.is_dir() or not any(path.is_file() for path in known):
            raise ValueError("所选目录必须包含 config.json 或 state.json；请选择旧版 data 目录。")
        if any(path.is_symlink() for path in known):
            raise ValueError("旧版配置或配对文件不能是符号链接。")
        self._save_directory_selection(directory)
        self.pending_data_dir = directory
        LOG.info("已保存下次启动的数据目录选择：%s；当前服务及实例不切换", directory)
        # 保留当前用户的自启偏好，只更新专属 Run 命令的目录参数；不在所选目录写偏好。
        try:
            self.autostart.sync(self.options.host, self.port, directory)
        except Exception as exc:
            LOG.exception("更新下次登录自启路径失败")
            show_error("目录选择已保存，但开机自启路径更新失败：" + str(exc)
                       + "\n请退出后手动重新启动；详情见日志。")
        self.refresh_view()
        messagebox.showinfo(
            "旧版目录已保存",
            "下次默认数据目录：" + str(directory)
            + "\n当前连接及原文件保持不变。请从托盘退出，再手动重新启动，不会自动创建新进程。"
            + "\n重启时请勿携带旧的 --data-dir 参数或 DESKTOUCH_DATA_DIR 环境变量。"
            + "\n旧配对的恢复取决于 state.json 与浏览器中保存的 token；请继续使用原来的完整地址。"
            + ("\n当前地址：" + self.url if self.url else "")
            + "\n若 IP 或端口不同，请恢复原来的 IP/端口后再连接。",
            parent=self.root,
        )

    def refresh_view(self):
        if self.root is None:
            return
        auth = self.app.state.auth
        seconds = max(0, int(auth.code_until - time.monotonic()))
        code = auth.code if seconds else "已过期，请刷新"
        local_only = bool(self.host and ipaddress.ip_address(self.host).is_loopback)
        self.status_var.set(self.status)
        self.url_var.set(self.url or "暂无连接地址")
        self.code_var.set(code)
        self._sync_address_choice()
        self.help_var.set(
            ("仅本机可访问；平板无法连接此地址。" if local_only else "平板与电脑连接同一可信局域网后，在浏览器打开上方地址。")
            + ("\n" + self._address_note if self._address_note else "")
            + ("\n当前使用虚拟网卡地址，手机通常无法访问；请在上方改选 Wi-Fi/以太网地址。" if self._virtual_host() else "")
            + "\n配对码剩余 %d 分 %02d 秒。已配对设备无需重新配对。" % divmod(seconds, 60)
            + ("\n演示模式：不会控制电脑或写入开机自启。" if self.options.demo else "")
            + "\n关闭窗口仅隐藏；退出请使用托盘菜单。"
            + ("\n已选择旧版目录，请退出后重启生效：" + str(self.pending_data_dir) if self.pending_data_dir else "")
        )
        view = (self.url, code)
        if view != self._last_view:
            self._last_view = view
            if self.url:
                import qrcode
                from PIL import ImageTk
                image = qrcode.make(self.url).convert("RGB").resize((160, 160))
                self.qr_image = ImageTk.PhotoImage(image, master=self.root)
                self.qr_label.configure(image=self.qr_image)
            else:
                self.qr_label.configure(image="")

    def _virtual_host(self):
        if not self.host:
            return False
        for row in self.address_rows:
            if row["address"] == self.host:
                return bool(row["virtual"])
        return False

    def _sync_address_choice(self):
        if self.options.host != "lan" or self.address_choice is None:
            return
        rows = self.address_rows or network.candidates()
        mapping = {network.label(row): row for row in rows}
        if self.host and ipaddress.ip_address(self.host).is_loopback:
            mapping = {"127.0.0.1 · 本机回环 · 仅电脑访问": {
                "address": "127.0.0.1", "interface": "本机回环", "virtual": False,
                "up": True, "default_route": False,
            }, **mapping}
        values = tuple(mapping)
        if values != self._address_values:
            self._address_values = values
            self.address_map = mapping
            self.address_choice.configure(values=values)
        for text, row in mapping.items():
            if row["address"] == self.host:
                if self.address_choice.get() != text:
                    self.address_choice.set(text)
                break

    def _build_window(self):
        import tkinter as tk
        from tkinter import ttk
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("DeskTouch · 连接信息")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="DeskTouch", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        self.status_var = tk.StringVar(self.root)
        self.url_var = tk.StringVar(self.root)
        self.code_var = tk.StringVar(self.root)
        self.help_var = tk.StringVar(self.root)
        ttk.Label(frame, textvariable=self.status_var, wraplength=440).pack(anchor="w", pady=(8, 10))
        address = ttk.Entry(frame, textvariable=self.url_var, width=54, state="readonly")
        address.pack(fill="x")
        self.qr_label = ttk.Label(frame)
        self.qr_label.pack(pady=10)
        ttk.Label(frame, text="6 位配对码（10 分钟有效）").pack()
        ttk.Label(frame, textvariable=self.code_var, font=("Consolas", 26, "bold")).pack()
        ttk.Label(frame, textvariable=self.help_var, wraplength=440).pack(anchor="w", pady=12)
        ttk.Label(frame, text="选择手机访问使用的网卡地址（改选后自动重启服务）").pack(anchor="w")
        self.address_choice = ttk.Combobox(frame, state="readonly", width=52)
        self.address_choice.pack(fill="x", pady=(4, 0))
        self.address_choice.bind("<<ComboboxSelected>>", lambda event: self._dispatch(self.apply_address_choice))
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        for text, action in (("刷新配对码", self.refresh_code), ("打开面板", self.open_panel),
                             ("重试局域网", self.start_server), ("暂用本机", lambda: self.start_server(loopback=True))):
            ttk.Button(buttons, text=text, command=lambda action=action: self._dispatch(action)).pack(side="left", padx=2)
        ttk.Button(frame, text="使用旧版数据目录…", command=lambda: self._dispatch(self.select_legacy_directory)).pack(anchor="w", pady=(10, 0))
        ttk.Label(frame, text="日志：" + str(self.data_dir / "logs"), wraplength=440).pack(anchor="w", pady=(12, 0))
        self.root.report_callback_exception = self._callback_error
        self.refresh_view()

    def _callback_error(self, kind, value, tb):
        LOG.error("窗口回调失败", exc_info=(kind, value, tb))
        show_error(str(value) + "\n日志：" + str(self.data_dir / "logs"))

    def _build_tray(self):
        import pystray
        from PIL import Image
        from .main import ROOT
        menu = pystray.Menu(
            pystray.MenuItem("查看连接信息", lambda icon, item: self.post(self.show_window), default=True),
            pystray.MenuItem("刷新 6 位配对码", lambda icon, item: self.post(self.refresh_code)),
            pystray.MenuItem("打开面板", lambda icon, item: self.post(self.open_panel)),
            pystray.MenuItem("选择连接地址…", lambda icon, item: self.post(self.show_window)),
            pystray.MenuItem("重试局域网连接", lambda icon, item: self.post(self.start_server)),
            pystray.MenuItem("暂用 127.0.0.1（仅本机）", lambda icon, item: self.post(lambda: self.start_server(loopback=True))),
            pystray.MenuItem("开机自启（用户登录后）", lambda icon, item: self.post(self.toggle_autostart),
                             checked=lambda item: self.autostart.enabled, enabled=lambda item: self.autostart.allowed),
            pystray.MenuItem("使用旧版数据目录…", lambda icon, item: self.post(self.select_legacy_directory),
                             enabled=lambda item: not self.options.demo),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", lambda icon, item: self.post(self.quit)),
        )
        with Image.open(ROOT / "web" / "icon192.png") as image:
            self.icon = pystray.Icon("DeskTouch", image.copy(), "DeskTouch", menu)
        self.tray_thread = threading.Thread(target=self._run_tray, name="desktouch-tray", daemon=True)
        self.tray_thread.start()

    def _setup_tray(self, icon):
        # stop() 在 pystray 启动前无效；准备完成后检查退出状态，覆盖早期失败的竞态。
        if self.quitting:
            icon.stop()
        else:
            icon.visible = True
            if self.quitting:
                icon.stop()

    def _run_tray(self):
        try:
            if self.quitting:
                return
            self.icon.run(setup=self._setup_tray)
            if not self.quitting:
                raise RuntimeError("托盘意外停止，请退出后重新启动。")
        except Exception as exc:
            LOG.exception("托盘运行失败")
            message = str(exc)
            self.post(lambda: self._tray_failed(message))

    def _tray_failed(self, message):
        self.show_window()
        show_error("托盘不可用：" + message + "\n程序将退出，请检查日志后重试。")
        self.quit()

    def _dispatch(self, action):
        try:
            action()
        except Exception as exc:
            LOG.exception("桌面操作失败")
            self.status = "操作失败：" + str(exc)
            self._notify(self.status)
            self.refresh_view()
            show_error(self.status + "\n日志：" + str(self.data_dir / "logs"))

    def _tick(self):
        if self.quitting:
            return
        if self.instance.consume_show_request():
            self._dispatch(self.show_window)
        while not self.commands.empty():
            self._dispatch(self.commands.get_nowait())
            if self.quitting:
                return
        if self.server:
            if self.server.ready:
                mode = "仅本机，平板不可访问" if ipaddress.ip_address(self.host).is_loopback else "可信局域网"
                self.status = "服务运行中（%s）：%s" % (mode, self.url)
                if self.icon is not None:
                    self.icon.title = "DeskTouch · " + mode + " · " + self.url
                if self.test_ready_file is not None and not self._test_ready_written and not self._test_ready_failed:
                    try:
                        # 写入前再次解析路径，防止父目录后来被改成指向目录外的链接。
                        path = validate_test_options(self.options, self.app.state.data_dir)
                        atomic_json(path, {"code": self.app.state.auth.code, "demo": True,
                                           "pid": os.getpid(), "window_handle": self.root.winfo_id()})
                        self._test_ready_written = True
                    except Exception as exc:
                        self._test_ready_failed = True
                        LOG.exception("桌面验收文件写入失败")
                        show_error("桌面验收文件写入失败：" + str(exc))
                        self.quit()
                        return
            elif not self.server.alive and not self._reported_server_error:
                self._reported_server_error = True
                self.status = "服务未运行：" + (self.server.error or "服务已停止，请重试。")
                LOG.error(self.status)
                self._notify(self.status)
                show_error(self.status + "\n可在连接窗口重试或暂用本机。\n日志：" + str(self.data_dir / "logs"))
        self.refresh_view()
        self.root.after(250, self._tick)

    def _close_modules(self):
        error = None
        for module in getattr(self.app.state, "modules", {}).values():
            close = getattr(module, "close", None)
            if callable(close):
                try:
                    close()
                except Exception as exc:
                    LOG.exception("应用模块清理失败")
                    error = error or exc
        if error is not None:
            raise error

    def _dispose_ui(self):
        self.quitting = True
        if self.root is not None and self._test_exit_timer is not None:
            try:
                self.root.after_cancel(self._test_exit_timer)
            except Exception:
                LOG.warning("取消验收退出定时器失败", exc_info=True)
            self._test_exit_timer = None
        try:
            if self.icon is not None:
                self.icon.stop()
        finally:
            try:
                if self.tray_thread is not None and self.tray_thread.ident is not None:
                    self.tray_thread.join(timeout=5)
                    if self.tray_thread.is_alive():
                        LOG.error("托盘线程未及时结束")
            finally:
                if self.root is not None:
                    root, self.root = self.root, None
                    root.destroy()

    def quit(self):
        if self.server is not None:
            self.server.stop()
        try:
            self._close_modules()
        finally:
            self._dispose_ui()

    def run(self):
        try:
            self._build_window()
            self._build_tray()
            try:
                self.autostart.sync(self.options.host, self.port, self.data_dir)
            except Exception as exc:
                LOG.exception("开机自启配置失败")
                show_error("开机自启配置失败：" + str(exc) + "\n桌面服务仍可使用，详情请查看日志。")
            self._dispatch(self.start_server)
            if not self.options.background:
                self.show_window()
            self.root.after(250, self._tick)
            if self.options.test_exit_after is not None:
                self._test_exit_timer = self.root.after(
                    max(1, int(self.options.test_exit_after * 1000)), lambda: self._dispatch(self.quit),
                )
            self.root.mainloop()
        finally:
            if not self.quitting:
                try:
                    self.quit()
                finally:
                    # 窗口创建到一半或服务清理报错时仍释放 tkinter 和托盘。
                    if not self.quitting:
                        self._dispose_ui()


class DesktopArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # 无控制台 exe 的参数错误也进入稳定文件日志及错误窗口。
        raise ValueError("启动参数无效：" + message)


def run_desktop(argv=None) -> int:
    parser = DesktopArgumentParser(description="DeskTouch Windows 连接窗口与托盘")
    parser.add_argument("--host", default="lan")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--background", action="store_true", help="用户登录时仅启动托盘")
    parser.add_argument("--test-ready-file", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--test-exit-after", type=float, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--headless", action="store_true", help="使用服务器 CLI，不创建窗口或托盘")
    parser.add_argument("--no-autostart", action="store_true", help="不读取或写入开机自启")
    arguments = list(argv) if argv is not None else sys.argv[1:]
    try:
        options = parser.parse_args(arguments)
    except ValueError as exc:
        if "--headless" in arguments:
            raise
        log_path = None
        try:
            from .storage import resolve_data_dir
            log_path = configure_logging(Path(resolve_data_dir(demo="--demo" in arguments)))
        except Exception:
            LOG.exception("无法为参数错误初始化日志")
        LOG.error("%s", exc)
        show_error(str(exc) + ("\n日志：" + str(log_path) if log_path else ""))
        return 1
    if options.headless:
        if options.test_exit_after is not None:
            raise ValueError("--test-exit-after 仅适用于桌面，不能与 --headless 一起使用。")
        from .main import run
        # 交给服务器 parser 解析其 CLI 参数；临时 argv 也使程序化测试保持隔离。
        previous = sys.argv
        sys.argv = [previous[0], *(list(argv) if argv is not None else previous[1:])]
        try:
            run()
        finally:
            sys.argv = previous
        return 0
    instance = None
    log_path = None
    try:
        from .storage import resolve_data_dir
        data_dir = Path(resolve_data_dir(options.data_dir, demo=options.demo))
        log_path = configure_logging(data_dir)
        validate_test_options(options, data_dir)
        require_user_session()
        if options.host != "lan":
            validate_host(options.host)
        if options.port is not None and not 1 <= options.port <= 65535:
            raise ValueError("端口必须在 1–65535 范围内。")
        instance = SingleInstance(data_dir)
        if not instance.primary:
            LOG.info("已通知现有实例显示连接窗口")
            return 0
        autostart = Autostart(data_dir, demo=options.demo, no_autostart=options.no_autostart)
        Desktop(options, data_dir, instance, autostart).run()
        return 0
    except Exception as exc:
        LOG.exception("DeskTouch 桌面启动失败")
        show_error("DeskTouch 启动失败：" + str(exc) + ("\n日志：" + str(log_path) if log_path else ""))
        return 1
    finally:
        if instance is not None:
            instance.close()
