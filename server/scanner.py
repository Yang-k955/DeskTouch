from __future__ import annotations

import copy
import json
import ntpath
import os
import re
import threading
import time
from pathlib import Path

import psutil

from .common import DeskError, atomic_json, digest, identity
from .launcher import canonical_path, parse_args, resolve_target, valid_uri, visible_windows

try:
    import pythoncom
    import win32com.client as com_client
    import winreg
except ImportError:
    pythoncom = com_client = winreg = None

SOURCES = ("startmenu", "uwp", "steam", "running")
PREFIXES = {"startmenu": "sm", "uwp": "uwp", "steam": "steam", "running": "run"}
NOISE = re.compile(r"(?:^|[^a-z0-9])(?:uninstall(?:er)?|unins\d*|unins0\d*|update(?:r)?|setup|install(?:er)?|crashpad(?:_handler)?|crashreport(?:er)?|helper|repair|readme|help|documentation|website)(?:$|[^a-z0-9])", re.I)


def filtered(name, target):
    texts = (name, ntpath.basename(target))
    return any(NOISE.search(text) or any(word in text for word in ("官网", "卸载", "帮助")) for text in texts)


def parse_vdf(text):
    # Steam KeyValues：仅解析带引号的键值/嵌套块，不运行任何脚本。
    tokens = re.findall(r'"((?:\\.|[^"\\])*)"|([{}])|(?P<comment>//[^\n]*)', text)
    stream = []
    for quoted, brace, comment in tokens:
        if not comment:
            stream.append(brace or quoted.replace('\\"', '"').replace('\\\\', '\\'))
    root, stack, key = {}, [], None
    current = root
    for token in stream:
        if token == "{":
            if key is None or len(stack) >= 16:
                raise ValueError("Steam 元数据嵌套无效")
            child = {}
            current[key] = child
            stack.append(current)
            current, key = child, None
        elif token == "}":
            if not stack or key is not None:
                raise ValueError("Steam 元数据括号无效")
            current, key = stack.pop(), None
        elif key is None:
            key = token
        else:
            current[key], key = token, None
    if stack or key is not None:
        raise ValueError("Steam 元数据不完整")
    return root


def read_vdf(path):
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("Steam 元数据超过大小限制")
    return parse_vdf(path.read_text(encoding="utf-8-sig", errors="replace"))


class Scanner:
    def __init__(self, data_dir: Path, demo=False):
        self.path = Path(data_dir) / "scan_cache.json"
        self.demo = bool(demo)
        self._lock = threading.RLock()
        self._candidates = {}
        self._cache = None

    def _menu_roots(self):
        roots = []
        for variable in ("ProgramData", "APPDATA"):
            value = os.environ.get(variable)
            if value:
                roots.append(Path(value) / "Microsoft/Windows/Start Menu/Programs")
        return roots

    def _menu_files(self):
        files = []
        for root in self._menu_roots():
            if not root.is_dir():
                continue
            for directory, dirs, names in os.walk(root, followlinks=False):
                base = Path(directory)
                dirs[:] = sorted(d for d in dirs if not (base / d).is_symlink() and not getattr(base / d, "is_junction", lambda: False)() and (base / d).resolve().is_relative_to(root.resolve()))
                for name in sorted(names):
                    path = base / name
                    if path.suffix.lower() in {".lnk", ".url"} and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()):
                        files.append(path)
                        if len(files) >= 4000:
                            return files
        return files

    def _steam_roots(self):
        roots = []
        if winreg is None:
            return roots
        for hive, key, field in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"), (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath")):
            try:
                with winreg.OpenKey(hive, key) as handle:
                    value, _ = winreg.QueryValueEx(handle, field)
                if isinstance(value, str) and Path(value).is_dir():
                    roots.append(Path(value))
            except OSError:
                continue
        return list(dict.fromkeys(roots))

    def _steam_files(self):
        files, libraries = [], []
        for root in self._steam_roots():
            libraries.append(root)
            config = root / "steamapps/libraryfolders.vdf"
            if config.is_file():
                files.append(config)
                try:
                    entries = read_vdf(config).get("libraryfolders", {})
                    for key, entry in list(entries.items())[:64]:
                        if key.isdigit():
                            value = entry.get("path") if isinstance(entry, dict) else entry
                            if isinstance(value, str) and Path(value).is_absolute():
                                libraries.append(Path(value))
                except (OSError, ValueError, AttributeError):
                    pass
        for root in list(dict.fromkeys(libraries))[:64]:
            directory = root / "steamapps"
            if directory.is_dir():
                for path in sorted(directory.glob("appmanifest_*.acf"))[:3000]:
                    if path.is_file() and not path.is_symlink():
                        files.append(path)
                    if len(files) >= 4000:
                        return files
        return files

    def _metadata(self, menu, steam):
        rows = []
        for path in [*self._menu_roots(), *menu, *steam]:
            try:
                stat = path.stat()
                rows.append((str(path), stat.st_mtime_ns, stat.st_size))
            except OSError:
                rows.append((str(path), None, None))
        return digest(json.dumps(rows, ensure_ascii=False))

    def _candidate(self, source, name, target, kind, args=None, **extra):
        candidate = {"name": name, "source": source, "target": target, "suggested_type": kind, "args": parse_args(args or []), "process": extra.pop("process", ""), **extra}
        candidate["key"] = PREFIXES[source] + ":" + digest(identity(candidate))
        return candidate

    def _startmenu(self, paths):
        result, warnings = [], []
        wscript = com_client.Dispatch("WScript.Shell") if com_client is not None else None
        for path in paths:
            try:
                if filtered(path.stem, ""):
                    continue
                if path.suffix.lower() == ".url":
                    import configparser
                    parser = configparser.ConfigParser(interpolation=None)
                    parser.read(path, encoding="utf-8-sig")
                    target = parser.get("InternetShortcut", "URL", fallback="")
                    if valid_uri(target):
                        result.append(self._candidate("startmenu", path.stem, target, "uri"))
                    continue
                if wscript is None:
                    continue
                link = wscript.CreateShortCut(str(path))
                target = os.path.expandvars(link.TargetPath or "")
                args = parse_args(link.Arguments or "")
                cwd = link.WorkingDirectory or ""
                icon = link.IconLocation or ""
                del link
                if target:
                    target = resolve_target(target)
                if not target or filtered(path.stem, target):
                    continue
                if ntpath.splitext(target)[1].lower() not in {".exe", ".cmd", ".bat"} or not Path(target).is_file():
                    continue
                # 快捷方式可能保留已失效的工作目录（如 Electron 升级后旧 app-<版本>），只保存仍然存在的。
                workdir = cwd if cwd and Path(cwd).is_dir() else ntpath.dirname(target)
                # advertised/MSI 链接仍通过 .lnk 启动；解析目标只用于识别和去重。
                canon = identity({"type": "exe", "path": canonical_path(target), "args": args})
                result.append(self._candidate("startmenu", path.stem, str(path), "shell", args, process=ntpath.basename(target), process_path=target, cwd=workdir, icon_path=icon or target, _canonical=canon))
            except Exception as exc:
                warnings.append("开始菜单条目读取失败：" + path.name + "：" + str(exc))
        return result, warnings

    def _uwp(self):
        if com_client is None:
            return [], ["AppsFolder COM 不可用"]
        result = []
        application = com_client.Dispatch("Shell.Application")
        folder = application.NameSpace("shell:AppsFolder")
        if folder is None:
            return [], ["无法读取 AppsFolder"]
        for index, item in enumerate(folder.Items()):
            if index >= 4000:
                break
            aumid = item.ExtendedProperty("System.AppUserModel.ID") or item.Path
            # AppsFolder 同时包含桌面软件，不能把其普通路径当作 AUMID。
            if isinstance(aumid, str) and re.fullmatch(r"[A-Za-z0-9_.-]+![A-Za-z0-9_.-]+", aumid) and not filtered(item.Name, ""):
                result.append(self._candidate("uwp", item.Name, aumid, "uwp"))
        return result, []

    def _steam(self, paths):
        result, warnings = [], []
        for path in paths:
            if path.suffix.lower() != ".acf":
                continue
            try:
                state = read_vdf(path).get("AppState", {})
                appid, name = state.get("appid", ""), state.get("name", "")
                if re.fullmatch(r"\d{1,10}", appid) and name and not filtered(name, ""):
                    result.append(self._candidate("steam", name, "steam://rungameid/" + appid, "uri"))
            except (OSError, ValueError, AttributeError, TypeError) as exc:
                warnings.append("Steam 元数据读取失败：" + path.name + "：" + str(exc))
        return result, warnings

    def _running(self):
        result, seen = [], set()
        for _, pid, title in visible_windows():
            if pid in seen:
                continue
            seen.add(pid)
            try:
                proc = psutil.Process(pid)
                target, name = proc.exe(), proc.name()
                if target and not filtered(name, target):
                    result.append(self._candidate("running", title or ntpath.splitext(name)[0], target, "exe", process=name, process_path=target, cwd=ntpath.dirname(target)))
            except (psutil.Error, OSError):
                continue
        return result, []

    def _dedupe(self, items):
        selected = {}
        priority = {"startmenu": 0, "uwp": 1, "steam": 2, "running": 3}
        for item in items:
            canonical = item.get("_canonical") or identity({**item, "target": canonical_path(item["target"]) if item["suggested_type"] in {"exe", "shell", "cmd"} else item["target"]})
            rank = (priority[item["source"]], len(item["name"]), len(Path(item["target"]).parts), item["target"].casefold())
            previous = selected.get(canonical)
            if previous is None or rank < previous[0]:
                selected[canonical] = (rank, item)
        return sorted((pair[1] for pair in selected.values()), key=lambda item: (item["name"].casefold(), item["key"]))

    def _demo_items(self):
        return [self._candidate("startmenu", "演示 · 编辑器（模拟）", r"C:\Demo\Editor.lnk", "shell"), self._candidate("uwp", "演示 · 音乐（模拟）", "DeskTouchDemo_000!Music", "uwp"), self._candidate("steam", "演示 · 游戏（模拟）", "steam://rungameid/0", "uri"), self._candidate("running", "演示 · 运行应用（模拟）", r"C:\Demo\Running.exe", "exe")]

    def scan(self, refresh=False):
        with self._lock:
            if self.demo:
                items = self._demo_items()
                result = {"cached": False, "scanned_at": int(time.time() * 1000), "counts": {source: 1 for source in SOURCES}, "items": items, "warnings": ["演示模式：全部候选为静态模拟，未扫描本机"], "demo": True}
                self._candidates = {item["key"]: item for item in items}
                return copy.deepcopy(result)
            menu, steam = self._menu_files(), self._steam_files()
            fingerprint = self._metadata(menu, steam)
            now = int(time.time() * 1000)
            if self._cache is None and self.path.is_file():
                try:
                    if self.path.stat().st_size > 16 * 1024 * 1024:
                        raise ValueError("扫描缓存过大")
                    loaded = json.loads(self.path.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict) and isinstance(loaded.get("items"), list) and all(isinstance(item, dict) and item.get("source") in SOURCES and all(isinstance(item.get(key), str) for key in ("key", "name", "target", "suggested_type")) for item in loaded["items"]):
                        self._cache = loaded
                except (OSError, ValueError):
                    pass
            cache = self._cache
            cached = bool(not refresh and cache and cache.get("fingerprint") == fingerprint and isinstance(cache.get("scanned_at"), int) and 0 <= now - cache["scanned_at"] < 24 * 3600 * 1000)
            warnings = list(cache.get("warnings", [])) if cached else []
            if cached:
                static = copy.deepcopy(cache["items"])
                scanned_at = cache["scanned_at"]
            else:
                static = []
                initialized = False
                try:
                    if pythoncom is not None:
                        pythoncom.CoInitialize()
                        initialized = True
                    for source, method, values in (("startmenu", self._startmenu, (menu,)), ("uwp", self._uwp, ())):
                        try:
                            found, messages = method(*values)
                            static.extend(found)
                            warnings.extend(messages)
                        except Exception as exc:
                            warnings.append(source + " 扫描失败：" + str(exc))
                except Exception as exc:
                    warnings.append("扫描 COM 初始化失败：" + str(exc))
                finally:
                    if initialized:
                        pythoncom.CoUninitialize()
                try:
                    found, messages = self._steam(steam)
                    static.extend(found)
                    warnings.extend(messages)
                except Exception as exc:
                    warnings.append("steam 扫描失败：" + str(exc))
                static = self._dedupe(static)
                scanned_at = now
                self._cache = {"scanned_at": now, "fingerprint": fingerprint, "items": static, "warnings": warnings}
                try:
                    atomic_json(self.path, self._cache)
                except OSError as exc:
                    warnings = [*warnings, "扫描缓存保存失败：" + str(exc)]
            try:
                running, messages = self._running()
                warnings.extend(messages)
            except Exception as exc:
                running = []
                warnings.append("运行窗口读取失败：" + str(exc))
            items = self._dedupe([*static, *running])
            self._candidates = {item["key"]: item for item in items}
            counts = {source: sum(item["source"] == source for item in items) for source in SOURCES}
            return copy.deepcopy({"cached": cached, "scanned_at": scanned_at, "counts": counts, "items": items, "warnings": warnings})

    def resolve(self, key):
        with self._lock:
            if not isinstance(key, str) or key not in self._candidates:
                raise DeskError("unknown_candidate", "扫描候选不存在，请重新扫描", 404)
            return copy.deepcopy(self._candidates[key])
