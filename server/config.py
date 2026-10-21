from __future__ import annotations

import copy
import json
import ntpath
import re
import threading
from pathlib import Path

from .common import DeskError, atomic_json, digest, identity

ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
TYPES = {"app", "stat", "volume", "media", "power"}
METRICS = {"cpu", "memory", "disk", "network", "uptime", "battery", "foreground"}


def defaults():
    return {
        "server": {"host": "127.0.0.1", "port": 8000, "max_clients": 3, "push_interval_ms": 1000, "preferred_host": ""},
        "ui": {"columns": 4, "rows": 3, "theme": "light", "accent": "#3465d9", "keep_awake": False},
        "pages": [
            {"id": "main", "name": "总览", "items": [
                {"type": "stat", "metric": "cpu", "span": 2},
                {"type": "stat", "metric": "memory", "span": 1},
                {"type": "stat", "metric": "network", "span": 1},
                {"type": "volume", "span": 2}, {"type": "media", "span": 2},
                {"type": "stat", "metric": "disk", "span": 2},
                {"type": "power", "span": 2, "actions": ["lock", "display_off", "sleep", "restart", "shutdown"]}]},
            {"id": "apps", "name": "快捷应用", "items": []}],
        "apps": {},
    }


def validate(data):
    if not isinstance(data, dict):
        raise DeskError("invalid_config", "配置必须是 JSON 对象")
    server, ui = data.get("server", {}), data.get("ui", {})
    if not isinstance(server, dict) or not isinstance(ui, dict):
        raise DeskError("invalid_config", "server 与 ui 必须为对象")
    for field, lo, hi, default in [("port", 1024, 65535, 8000), ("max_clients", 1, 10, 3), ("push_interval_ms", 500, 5000, 1000)]:
        val = server.get(field, default)
        if type(val) is not int or not lo <= val <= hi:
            raise DeskError("invalid_config", "server." + field + " 超出范围")
    preferred = server.get("preferred_host", "")
    if preferred not in (None, ""):
        import ipaddress
        if not isinstance(preferred, str):
            raise DeskError("invalid_config", "server.preferred_host 必须是字符串")
        try:
            address = ipaddress.ip_address(preferred)
        except ValueError:
            raise DeskError("invalid_config", "server.preferred_host 必须是 IPv4 地址")
        if address.version != 4 or address.is_loopback or address.is_link_local or address.is_unspecified or not address.is_private:
            raise DeskError("invalid_config", "server.preferred_host 必须是私有局域网 IPv4")
    for field, hi in [("columns", 8), ("rows", 10)]:
        if type(ui.get(field)) is not int or not 1 <= ui[field] <= hi:
            raise DeskError("invalid_config", "ui." + field + " 超出范围")
    if ui.get("theme") not in {"light", "dark"} or not re.fullmatch(r"#[0-9a-fA-F]{6}", ui.get("accent", "")):
        raise DeskError("invalid_config", "主题或强调色无效")
    apps, pages = data.get("apps"), data.get("pages")
    if not isinstance(apps, dict) or not isinstance(pages, list) or not pages:
        raise DeskError("invalid_config", "apps 或 pages 格式无效")
    for key, app in apps.items():
        if not isinstance(app, dict) or not ID.fullmatch(key) or app.get("type") not in {"exe", "shell", "uwp", "uri", "cmd"} or not app.get("path"):
            raise DeskError("invalid_config", "应用配置无效：" + key)
        from .icon_library import GLYPHS
        if app.get("icon_id") is not None and app["icon_id"] not in GLYPHS:
            raise DeskError("invalid_config", "应用默认图标无效：" + key)
        args = app.get("args", [])
        if not isinstance(args, (list, str)) or (isinstance(args, list) and any(not isinstance(x, str) for x in args)):
            raise DeskError("invalid_config", "args 应为字符串数组：" + key)
    ids = set()
    for page in pages:
        if not isinstance(page, dict) or not ID.fullmatch(page.get("id", "")) or page["id"] in ids or not isinstance(page.get("items"), list):
            raise DeskError("invalid_config", "页面 ID 重复或格式错误")
        ids.add(page["id"])
        for item in page["items"]:
            if not isinstance(item, dict) or item.get("type") not in TYPES or type(item.get("span", 1)) is not int or not 1 <= item.get("span", 1) <= 8:
                raise DeskError("invalid_config", "卡片类型或跨列数无效")
            if item["type"] == "app" and item.get("app_id") not in apps:
                raise DeskError("invalid_config", "卡片引用不存在的应用")
            if item["type"] == "stat" and item.get("metric") not in METRICS:
                raise DeskError("invalid_config", "状态指标无效")
    return data


class Config:
    def __init__(self, data_dir: Path):
        self.path = data_dir / "config.json"
        self.lock = threading.RLock()
        if not self.path.exists():
            atomic_json(self.path, defaults())
        self.reload()

    def reload(self):
        with self.lock:
            try:
                new = validate(json.loads(self.path.read_text(encoding="utf-8-sig")))
            except (ValueError, TypeError, KeyError) as exc:
                raise DeskError("invalid_config", "配置格式错误：" + str(exc)) from exc
            self.data = new
            self.mtime = self.path.stat().st_mtime_ns
        return self.snapshot()

    def reload_if_changed(self):
        if self.path.stat().st_mtime_ns != self.mtime:
            self.reload()

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.data)

    def _save(self, new):
        validate(new)
        atomic_json(self.path, new)
        self.data = new
        self.mtime = self.path.stat().st_mtime_ns

    def add_candidates(self, candidates: list, page_id: str, group: str = "常用"):
        with self.lock:
            new = self.snapshot()
            page = next((p for p in new["pages"] if p["id"] == page_id), None)
            if page is None:
                raise DeskError("unknown_page", "页面不存在", 404)
            seen = {identity(a): key for key, a in new["apps"].items()}
            result = []
            for candidate in candidates:
                ident = identity(candidate)
                if ident in seen:
                    result.append({"key": candidate["key"], "app_id": seen[ident], "added": False})
                    continue
                app_id = "app_" + digest(ident)
                cfg = {"name": candidate["name"], "type": candidate["suggested_type"], "path": candidate["target"], "args": candidate.get("args", []), "process": candidate.get("process", ""), "group": group, "source": candidate["source"], "icon_key": candidate["key"]}
                if candidate.get("icon_path"):
                    cfg["icon_path"] = candidate["icon_path"]
                if candidate.get("cwd") and Path(candidate["cwd"]).is_dir():
                    cfg["cwd"] = candidate["cwd"]
                if candidate.get("process_path"):
                    cfg["process_path"] = candidate["process_path"]
                new["apps"][app_id] = cfg
                page["items"].append({"type": "app", "app_id": app_id, "span": 1})
                seen[ident] = app_id
                result.append({"key": candidate["key"], "app_id": app_id, "added": True})
            self._save(new)
            return result

    def remove(self, app_id):
        with self.lock:
            new = self.snapshot()
            if app_id not in new["apps"]:
                raise DeskError("unknown_app", "应用不存在", 404)
            del new["apps"][app_id]
            for page in new["pages"]:
                page["items"] = [i for i in page["items"] if i.get("app_id") != app_id]
            self._save(new)

    def set_preferred_host(self, host):
        with self.lock:
            new = self.snapshot()
            new["server"]["preferred_host"] = host or ""
            self._save(new)
            return new["server"]["preferred_host"]

    def add_custom(self, name, target, kind, icon_id=None, page_id="apps", group="常用"):
        """Add a user-picked executable. Path is validated by the caller (server side only)."""
        with self.lock:
            new = self.snapshot()
            page = next((p for p in new["pages"] if p["id"] == page_id), None)
            if page is None:
                raise DeskError("unknown_page", "页面不存在", 404)
            ident = identity({"type": kind, "path": target, "args": []})
            seen = {identity(a): key for key, a in new["apps"].items()}
            if ident in seen:
                raise DeskError("duplicate", "该启动地址已在面板中", 409)
            app_id = "app_" + digest(ident)
            cfg = {"name": name, "type": kind, "path": target, "args": [], "group": group, "source": "custom"}
            if icon_id:
                from .icon_library import GLYPHS
                if icon_id not in GLYPHS:
                    raise DeskError("unknown_icon", "默认图标不存在", 404)
                cfg["icon_id"] = icon_id
            if kind in {"exe", "cmd"}:
                cfg["process_path"] = target
            if kind in {"exe", "cmd", "shell"}:
                folder = ntpath.dirname(target)
                if Path(folder).is_dir():
                    cfg["cwd"] = folder
            new["apps"][app_id] = cfg
            page["items"].append({"type": "app", "app_id": app_id, "span": 1})
            self._save(new)
            return app_id

    def update_app(self, app_id, changes):
        with self.lock:
            new = self.snapshot()
            app = new["apps"].get(app_id)
            if app is None:
                raise DeskError("unknown_app", "应用不存在", 404)
            if "name" in changes and changes["name"]:
                app["name"] = changes["name"]
            if "path" in changes and changes["path"]:
                kind = changes.get("type") or app["type"]
                app.update({"path": changes["path"], "type": kind})
                if kind in {"exe", "cmd"}:
                    app["process_path"] = changes["path"]
                folder = ntpath.dirname(changes["path"])
                if kind in {"exe", "cmd", "shell"} and Path(folder).is_dir():
                    app["cwd"] = folder
                else:
                    app.pop("cwd", None)
            if "icon_id" in changes:
                from .icon_library import GLYPHS
                if changes["icon_id"] is not None and changes["icon_id"] not in GLYPHS:
                    raise DeskError("unknown_icon", "默认图标不存在", 404)
                app["icon_id"] = changes["icon_id"]
            self._save(new)
            return app

    def set_icon(self, app_id, icon_id):
        with self.lock:
            new = self.snapshot()
            if app_id not in new["apps"]:
                raise DeskError("unknown_app", "应用不存在", 404)
            from .icon_library import GLYPHS
            if icon_id is not None and icon_id not in GLYPHS:
                raise DeskError("unknown_icon", "默认图标不存在", 404)
            new["apps"][app_id]["icon_id"] = icon_id
            self._save(new)

    def layout(self, ui=None, pages=None):
        with self.lock:
            new = self.snapshot()
            if ui is not None:
                new["ui"].update(ui)
            if pages is not None:
                new["pages"] = pages
            self._save(new)
            return self.snapshot()
