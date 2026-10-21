from __future__ import annotations

import ctypes
import ntpath
import os
import re
import subprocess
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

import psutil

from .common import DeskError, identity

try:
    import win32api
    import win32con
    import win32gui
    import win32process
except ImportError:
    win32api = win32con = win32gui = win32process = None

URI_SCHEMES = {"http", "https", "steam", "spotify", "discord", "ms-settings", "mailto", "tel", "zoommtg", "msteams", "vscode"}
VERSION_DIR = re.compile(r"^app-\d+(?:[.\-]\d+)*$", re.IGNORECASE)


def resolve_target(target: str) -> str:
    """Repair Electron/Squirrel layouts: stub exe missing, real exe under app-<version>.

    Only same-name executables inside versioned sub-folders are considered, then a
    single unambiguous exe beside the shortcut. Anything else is returned unchanged.
    """
    if not isinstance(target, str) or not target:
        return target
    if Path(target).is_file():
        return target
    folder, name = Path(ntpath.dirname(target)), ntpath.basename(target)
    if not name or not folder.is_dir():
        return target
    found = []
    try:
        for child in folder.iterdir():
            if child.is_dir() and VERSION_DIR.match(child.name):
                candidate = child / name
                if candidate.is_file():
                    found.append(candidate)
    except OSError:
        return target
    if found:
        def version_key(path):
            return [int(part) for part in re.findall(r"\d+", path.parent.name)]
        return str(sorted(found, key=version_key)[-1])
    try:
        exes = [item for item in folder.iterdir() if item.is_file() and item.suffix.casefold() == ".exe"]
    except OSError:
        return target
    return str(exes[0]) if len(exes) == 1 else target


def parse_args(value):
    if value is None or value == "":
        return []
    if isinstance(value, list) and all(isinstance(arg, str) and "\x00" not in arg for arg in value):
        return list(value)
    if not isinstance(value, str) or "\x00" in value:
        raise DeskError("invalid_args", "args 必须是字符串数组或 Windows 命令行")
    if os.name != "nt":
        raise DeskError("module_unavailable", "旧字符串参数需要 Windows CommandLineToArgvW", 503)
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    shell32.CommandLineToArgvW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
    shell32.CommandLineToArgvW.restype = ctypes.POINTER(ctypes.c_wchar_p)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    count = ctypes.c_int()
    argv = shell32.CommandLineToArgvW('desktouch.exe ' + value, ctypes.byref(count))
    if not argv:
        raise DeskError("invalid_args", "Windows 无法解析命令行参数")
    try:
        return [argv[index] for index in range(1, count.value)]
    finally:
        kernel32.LocalFree(ctypes.cast(argv, ctypes.c_void_p))


def canonical_path(value):
    return ntpath.normcase(ntpath.normpath(os.path.expandvars(value))).casefold()


def valid_uri(target):
    if not isinstance(target, str) or any(ord(char) < 32 for char in target):
        return False
    try:
        parts = urlsplit(target)
        return parts.scheme.casefold() in URI_SCHEMES and bool(target.split(":", 1)[1]) and (parts.scheme not in {"http", "https"} or bool(parts.hostname))
    except ValueError:
        return False


def matching_pids(app):
    path = app.get("process_path")
    name = app.get("process", "")
    if not path and not name:
        return set()
    matches = set()
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            info = proc.info
            if path:
                match = bool(info.get("exe")) and canonical_path(info["exe"]) == canonical_path(path)
            else:
                match = (info.get("name") or "").casefold() == ntpath.basename(name).casefold()
            if match:
                matches.add(info["pid"])
        except (psutil.Error, OSError):
            continue
    return matches


def visible_windows(pids=None):
    windows = []
    if win32gui is None:
        return windows

    def visit(hwnd, _):
        try:
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                if pids is None or pid in pids:
                    windows.append((hwnd, pid, win32gui.GetWindowText(hwnd)))
        except Exception:
            pass
        return True

    win32gui.EnumWindows(visit, None)
    return windows


class Launcher:
    def __init__(self):
        self._guard = threading.Lock()
        self._locks = {}
        self._recent = {}

    def _process_app(self, app):
        if not app.get("process_path") and not app.get("process") and app.get("type") in {"exe", "cmd"}:
            return {**app, "process_path": app["path"]}
        if app.get("process_path") and not Path(app["process_path"]).is_file():
            return {**app, "process_path": resolve_target(app["process_path"])}
        return app

    def running(self, app):
        return bool(matching_pids(self._process_app(app)))

    def _focus(self, pids):
        for hwnd, _, _ in visible_windows(pids):
            try:
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                if win32gui.GetForegroundWindow() == hwnd:
                    return True
            except Exception:
                continue
        return False

    def _start(self, app, args):
        kind, target = app.get("type"), app.get("path")
        if not isinstance(target, str) or not target or "\x00" in target:
            raise DeskError("launch_failed", "启动目标无效", 400)
        if kind not in {"exe", "cmd", "shell", "uwp", "uri"}:
            raise DeskError("launch_failed", "不支持的应用类型", 400)
        cwd = app.get("cwd") or (ntpath.dirname(target) if kind in {"exe", "cmd", "shell"} else None)
        resolved = target
        if kind in {"exe", "cmd", "shell"}:
            resolved = resolve_target(target)
            if not Path(resolved).is_file():
                raise DeskError("launch_failed", "文件不存在：" + target, 404)
            if not cwd or not Path(cwd).is_dir():
                # Stale shortcut working directory must not block launching a valid exe.
                fallback = ntpath.dirname(resolved)
                cwd = fallback if Path(fallback).is_dir() else None
        if kind == "uri":
            if not valid_uri(target):
                raise DeskError("launch_failed", "不允许的协议链接", 400)
            os.startfile(target)
            return
        if kind == "uwp":
            if not re.fullmatch(r"[A-Za-z0-9_.-]+![A-Za-z0-9_.-]+", target):
                raise DeskError("launch_failed", "AUMID 无效", 400)
            explorer = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "explorer.exe")
            subprocess.Popen([explorer, "shell:AppsFolder\\" + target], shell=False)
            return
        if kind == "shell" or app.get("admin"):
            if win32api is None:
                raise DeskError("module_unavailable", "Windows Shell 不可用", 503)
            # 快捷方式自带参数；再次传入会造成重复或改变 advertised shortcut 的语义。
            params = "" if kind == "shell" and target.lower().endswith(".lnk") else subprocess.list2cmdline(args)
            result = win32api.ShellExecute(0, "runas" if app.get("admin") else "open", target, params, cwd, 1)
            if result <= 32:
                raise DeskError("launch_failed", "Windows Shell 启动失败：" + str(result), 500)
            return
        child = subprocess.Popen([resolved, *args], cwd=cwd or None, shell=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        code = child.poll()
        if code not in (None, 0):
            raise DeskError("launch_failed", "程序退出，退出码：" + str(code), 500)

    def launch(self, app):
        start = time.monotonic()
        args = parse_args(app.get("args", []))
        normalized = {**app, "args": args}
        ident = identity(normalized)
        with self._guard:
            lock = self._locks.setdefault(ident, threading.Lock())
        with lock:
            try:
                pids = matching_pids(self._process_app(app))
                if pids:
                    action = "focused" if self._focus(pids) else "already_running"
                elif time.monotonic() - self._recent.get(ident, -float("inf")) < 1.0:
                    # 进程可能尚未登记；合并短时间重复请求，不谎称窗口已激活。
                    action = "started"
                else:
                    self._start(app, args)
                    self._recent[ident] = time.monotonic()
                    action = "started"
                return {"ok": True, "action": action, "elapsed_ms": round((time.monotonic() - start) * 1000)}
            except DeskError:
                raise
            except Exception as exc:
                raise DeskError("launch_failed", "启动失败：" + str(exc), 500) from exc
