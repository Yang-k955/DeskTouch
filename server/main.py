from __future__ import annotations

import argparse
import asyncio
import base64
import contextlib
import ipaddress
import logging
import os
import re
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from . import __version__
from .auth import Auth
from .common import DeskError, identity
from .config import Config
from .hub import Hub

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
LOG = logging.getLogger("desktouch")
ACTIONS = {"lock", "display_off", "sleep", "restart", "shutdown"}


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Pair(Body):
    code: str = Field(pattern=r"^\d{6}$")
    device_name: str = Field(default="平板", min_length=1, max_length=64)


class Volume(Body):
    value: int = Field(ge=0, le=100, strict=True)


class Mute(Body):
    muted: bool = Field(strict=True)


class Control(Body):
    action: str


class Confirmation(Control):
    nonce: str = Field(min_length=10, max_length=100)


class Batch(Body):
    keys: list[str] = Field(min_length=1, max_length=100)
    page_id: str = "apps"
    group: str = Field(default="常用", max_length=40)


class Add(Body):
    key: str
    page_id: str = "apps"
    group: str = Field(default="常用", max_length=40)
    name: str | None = Field(default=None, max_length=80)


class IconChoice(Body):
    icon_id: str | None = Field(default=None, max_length=32)


class CustomApp(Body):
    name: str = Field(min_length=1, max_length=80)
    path: str = Field(min_length=3, max_length=500)
    icon_id: str | None = Field(default=None, max_length=32)
    page_id: str = "apps"
    group: str = Field(default="常用", max_length=40)


class AppEdit(Body):
    name: str | None = Field(default=None, max_length=80)
    path: str | None = Field(default=None, max_length=500)
    icon_id: str | None = Field(default=None, max_length=32)


class Layout(Body):
    ui: dict | None = None
    pages: list[dict] | None = None


def local_addresses():
    from .network import all_private
    return all_private()


def create_app(data_dir: Path | None = None, demo: bool = False, adapters=None):
    from .audio import Audio
    from .icons import Icons
    from .launcher import Launcher
    from .media import Media
    from .monitor import Monitor
    from .power import Power
    from .scanner import Scanner

    from .storage import resolve_data_dir
    data_dir = resolve_data_dir(data_dir, demo=demo)
    cfg, auth = Config(data_dir), Auth(data_dir)
    adapters = adapters or {}
    modules = {
        "audio": adapters.get("audio") or Audio(), "monitor": adapters.get("monitor") or Monitor(),
        "media": adapters.get("media") or Media(), "launcher": adapters.get("launcher") or Launcher(),
        "power": adapters.get("power") or Power(), "scanner": adapters.get("scanner") or Scanner(data_dir, demo=demo),
        "icons": adapters.get("icons") or Icons(data_dir),
    }
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="dt-monitor")
    hub = Hub(auth, cfg.snapshot()["server"]["max_clients"])
    state = {}

    async def worker(func, *args):
        return await asyncio.get_running_loop().run_in_executor(pool, func, *args)

    async def sample():
        for name in ("monitor", "audio"):
            try:
                state["system" if name == "monitor" else name] = await worker(modules[name].snapshot)
            except Exception as exc:
                state["system" if name == "monitor" else name] = {"available": False, "message": str(exc)}
        try:
            state["media"] = await modules["media"].snapshot()
            cover = state["media"].get("cover", "")
            if cover.startswith("data:image/") and ";base64," in cover:
                import hashlib
                mime, raw = cover.split(";base64,", 1)
                blob = base64.b64decode(raw, validate=True)
                if len(blob) <= 512 * 1024:
                    cover_id = hashlib.sha256(blob).hexdigest()[:24]
                    state["covers"] = {cover_id: (blob, mime[5:])}
                    state["media"]["cover"] = "/api/media/cover/" + cover_id
                else:
                    state["media"].pop("cover", None)
        except Exception as exc:
            state["media"] = {"available": False, "active": False, "message": str(exc)}
        if demo:
            state["audio"] = {"available": True, "volume": state.get("demo_volume", 42), "muted": state.get("demo_mute", False), "device": "演示音频（不控制电脑）"}
            state["media"] = {"available": True, "active": False, "mode": "demo"}
        return {"type": "state", "ts": int(time.time() * 1000), "system": state.get("system", {}), "audio": state.get("audio", {}), "media": state.get("media", {}), "apps": state.get("apps", {})}

    async def collect():
        last_apps = 0
        while True:
            try:
                if time.monotonic() - last_apps > 5:
                    applications = cfg.snapshot()["apps"]
                    if demo:
                        state["apps"] = {key: False for key in applications}
                    else:
                        state["apps"] = await worker(lambda: {key: modules["launcher"].running(a) for key, a in applications.items()})
                    last_apps = time.monotonic()
                try:
                    old = cfg.mtime
                    cfg.reload_if_changed()
                    if cfg.mtime != old:
                        hub.max_clients = cfg.snapshot()["server"]["max_clients"]
                        await hub.broadcast({"type": "config_updated"})
                except Exception as exc:
                    LOG.warning("Configuration reload rejected: %s", exc)
                await hub.broadcast(await sample())
            except Exception:
                LOG.exception("Sampling failed")
            await asyncio.sleep(cfg.snapshot()["server"]["push_interval_ms"] / 1000)

    @asynccontextmanager
    async def lifespan(app):
        await sample()
        task = asyncio.create_task(collect())
        yield
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        await hub.close()
        pool.shutdown(wait=True, cancel_futures=True)
        for module in modules.values():
            if callable(getattr(module, "close", None)):
                module.close()

    app = FastAPI(title="DeskTouch", version=__version__, lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.auth, app.state.config, app.state.modules, app.state.hub, app.state.data_dir = auth, cfg, modules, hub, data_dir

    def token_check(request: Request):
        header = request.headers.get("authorization", "")
        token = header[7:] if header.startswith("Bearer ") else ""
        return auth.check(token)

    def safe_peer(host):
        try:
            addr = ipaddress.ip_address(host)
            return addr.is_loopback or (addr.version == 4 and (host.startswith("10.") or host.startswith("192.168.") or ipaddress.ip_address("172.16.0.0") <= addr <= ipaddress.ip_address("172.31.255.255")))
        except ValueError:
            return host == "testclient"

    def origin_ok(origin, host):
        if not origin:
            return True
        parsed = urlsplit(origin)
        return parsed.scheme in {"http", "https"} and parsed.netloc.lower() == host.lower()

    @app.middleware("http")
    async def security(request, call_next):
        if not safe_peer(request.client.host) or not origin_ok(request.headers.get("origin"), request.headers.get("host", "")):
            return JSONResponse({"ok": False, "error": "forbidden", "message": "仅支持可信局域网与同源访问"}, status_code=403)
        hostname = urlsplit("//" + request.headers.get("host", "")).hostname
        if hostname not in {"localhost", "testserver", socket.gethostname().lower(), *local_addresses()}:
            return JSONResponse({"ok": False, "error": "invalid_host", "message": "请使用电脑内网 IP 访问"}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; connect-src 'self'; script-src 'self'; frame-ancestors 'none'"
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(DeskError)
    async def error_handler(request, exc):
        return JSONResponse({"ok": False, "error": exc.error, "message": exc.message}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request, exc):
        return JSONResponse({"ok": False, "error": "invalid_request", "message": "参数无效，请检查输入范围"}, status_code=422)

    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        LOG.exception("Unhandled request exception")
        return JSONResponse({"ok": False, "error": "internal_error", "message": "操作失败，详情请查看电脑日志"}, status_code=500)

    @app.get("/api/health")
    def health():
        return {"ok": True, "hostname": socket.gethostname(), "version": __version__, "demo": demo}

    @app.post("/api/pair")
    def pair(body: Pair, request: Request):
        return auth.pair(body.code, body.device_name, request.client.host)

    @app.get("/api/layout", dependencies=[Depends(token_check)])
    def get_layout():
        data = cfg.snapshot()
        return {"ui": data["ui"], "pages": data["pages"], "hostname": socket.gethostname(), "version": __version__, "demo": demo}

    @app.put("/api/layout", dependencies=[Depends(token_check)])
    async def set_layout(body: Layout):
        if body.ui and set(body.ui) - {"theme", "accent", "columns", "rows", "keep_awake"}:
            raise DeskError("invalid_layout", "不支持的界面字段")
        cfg.layout(body.ui, body.pages)
        await hub.broadcast({"type": "config_updated"})
        return get_layout()

    @app.post("/api/layout/reload", dependencies=[Depends(token_check)])
    async def reload_layout():
        cfg.reload()
        await hub.broadcast({"type": "config_updated"})
        return {"ok": True}

    @app.get("/api/apps", dependencies=[Depends(token_check)])
    def apps():
        data = cfg.snapshot()["apps"]
        return {"groups": [{"id": g, "name": g} for g in sorted({a.get("group", "常用") for a in data.values()})], "apps": [{"id": key, "name": a["name"], "group": a.get("group", "常用"), "running": state.get("apps", {}).get(key, False), "icon": "/api/icons/" + key + ".png", "icon_id": a.get("icon_id")} for key, a in data.items()]}

    @app.post("/api/apps/{app_id}/launch", dependencies=[Depends(token_check)])
    def launch(app_id: str):
        application = cfg.snapshot()["apps"].get(app_id)
        if not application:
            raise DeskError("unknown_app", "应用不存在", 404)
        if demo:
            return {"ok": True, "action": "dispatched", "message": "演示模式：没有启动实际应用"}
        return modules["launcher"].launch(application)

    @app.delete("/api/apps/{app_id}", dependencies=[Depends(token_check)])
    async def remove(app_id: str):
        cfg.remove(app_id)
        await hub.broadcast({"type": "config_updated"})
        return {"ok": True}

    def scan_public(refresh=False):
        found = modules["scanner"].scan(refresh)
        added = {identity(a) for a in cfg.snapshot()["apps"].values()}
        public = [{"key": a["key"], "name": a["name"], "source": a["source"], "suggested_type": a["suggested_type"], "icon": "/api/scan/icon/" + a["key"] + ".png", "added": identity(a) in added} for a in found["items"]]
        return {**found, "items": public}

    @app.get("/api/scan", dependencies=[Depends(token_check)])
    def scan(refresh: bool = False):
        return scan_public(refresh)

    @app.post("/api/scan/refresh", dependencies=[Depends(token_check)])
    def refresh_scan():
        return scan_public(True)

    @app.post("/api/apps/batch", dependencies=[Depends(token_check)])
    async def batch(body: Batch):
        candidates = await asyncio.to_thread(lambda: [modules["scanner"].resolve(key) for key in body.keys])
        results = cfg.add_candidates(candidates, body.page_id, body.group)
        await hub.broadcast({"type": "config_updated"})
        return {"ok": True, "results": results}

    @app.post("/api/apps", dependencies=[Depends(token_check)])
    async def add(body: Add):
        candidate = dict(await asyncio.to_thread(modules["scanner"].resolve, body.key))
        if body.name:
            candidate["name"] = body.name
        row = cfg.add_candidates([candidate], body.page_id, body.group)[0]
        if not row["added"]:
            raise DeskError("duplicate", "该应用已在面板中", 409)
        await hub.broadcast({"type": "config_updated"})
        return {"ok": True, "app_id": row["app_id"]}

    @app.get("/api/icons/{app_id}.png", dependencies=[Depends(token_check)])
    def icon(app_id: str):
        a = cfg.snapshot()["apps"].get(app_id)
        if not a:
            raise DeskError("unknown_app", "图标不存在", 404)
        if a.get("icon_id"):
            from fastapi.responses import Response
            from .icon_library import svg
            return Response(svg(a["icon_id"]), media_type="image/svg+xml")
        path = modules["icons"].get(app_id, a["name"], a.get("icon_path") or a.get("path", ""))
        return FileResponse(path, media_type="image/png")

    @app.get("/api/drives", dependencies=[Depends(token_check)])
    def drives():
        from .browser import drives as list_drives
        return {"drives": list_drives()}

    @app.get("/api/browse", dependencies=[Depends(token_check)])
    def browse(path: str = ""):
        from .browser import listing
        return listing(path)

    @app.post("/api/apps/custom", dependencies=[Depends(token_check)])
    async def add_custom(body: CustomApp):
        from .browser import validate_launch_target
        target = await asyncio.to_thread(validate_launch_target, body.path)
        app_id = cfg.add_custom(body.name.strip(), target["path"], target["type"], body.icon_id, body.page_id, body.group)
        LOG.info("Custom app added: %s -> %s", body.name, target["path"])
        await hub.broadcast({"type": "config_updated"})
        return {"ok": True, "app_id": app_id}

    @app.put("/api/apps/{app_id}", dependencies=[Depends(token_check)])
    async def edit_app(app_id: str, body: AppEdit):
        from .browser import validate_launch_target
        changes = {}
        if body.name is not None and body.name.strip():
            changes["name"] = body.name.strip()
        if body.path is not None:
            target = await asyncio.to_thread(validate_launch_target, body.path)
            changes["path"], changes["type"] = target["path"], target["type"]
        if "icon_id" in body.model_fields_set:
            changes["icon_id"] = body.icon_id
        if not changes:
            raise DeskError("nothing_to_change", "没有需要修改的内容", 400)
        cfg.update_app(app_id, changes)
        LOG.info("App updated: %s -> %s", app_id, changes.get("path", "(no path change)"))
        await hub.broadcast({"type": "config_updated"})
        return {"ok": True}

    @app.get("/api/icon-library", dependencies=[Depends(token_check)])
    def icon_library():
        from .icon_library import library
        return {"icons": library()}

    @app.get("/api/icon-library/{icon_id}.svg", dependencies=[Depends(token_check)])
    def library_icon(icon_id: str):
        from fastapi.responses import Response
        from .icon_library import svg
        return Response(svg(icon_id), media_type="image/svg+xml")

    @app.put("/api/apps/{app_id}/icon", dependencies=[Depends(token_check)])
    async def choose_icon(app_id: str, body: IconChoice):
        cfg.set_icon(app_id, body.icon_id)
        await hub.broadcast({"type": "config_updated"})
        return {"ok": True}

    @app.get("/api/scan/icon/{key}.png", dependencies=[Depends(token_check)])
    def scan_icon(key: str):
        a = modules["scanner"].resolve(key)
        path = modules["icons"].get(key, a["name"], a.get("icon_path") or a["target"])
        return FileResponse(path, media_type="image/png")

    @app.get("/api/system", dependencies=[Depends(token_check)])
    def system():
        return state.get("system", {})

    @app.get("/api/audio", dependencies=[Depends(token_check)])
    def audio():
        return state.get("audio", {})

    @app.post("/api/audio/volume", dependencies=[Depends(token_check)])
    async def volume(body: Volume):
        if demo:
            state["demo_volume"] = body.value
            state["audio"]["volume"] = body.value
            return state["audio"]
        value = await asyncio.to_thread(modules["audio"].set_volume, body.value)
        if not value.get("available"):
            raise DeskError("module_unavailable", value.get("message", "音频不可用"), 503)
        state["audio"] = value
        return value

    @app.post("/api/audio/mute", dependencies=[Depends(token_check)])
    async def mute(body: Mute):
        if demo:
            state["demo_mute"] = body.muted
            state["audio"]["muted"] = body.muted
            return state["audio"]
        value = await asyncio.to_thread(modules["audio"].set_mute, body.muted)
        if not value.get("available"):
            raise DeskError("module_unavailable", value.get("message", "音频不可用"), 503)
        state["audio"] = value
        return value

    @app.get("/api/media/cover/{cover_id}", dependencies=[Depends(token_check)])
    def media_cover(cover_id: str):
        from fastapi.responses import Response
        row = state.get("covers", {}).get(cover_id)
        if not row:
            raise DeskError("unknown_cover", "封面已更新或不存在", 404)
        return Response(row[0], media_type=row[1])

    @app.get("/api/media", dependencies=[Depends(token_check)])
    def media():
        return state.get("media", {})

    @app.post("/api/media/control", dependencies=[Depends(token_check)])
    async def media_control(body: Control):
        if body.action not in {"play_pause", "next", "previous"}:
            raise DeskError("invalid_action", "媒体动作无效")
        if demo:
            return {"ok": True, "mode": "demo"}
        return await modules["media"].control(body.action)

    @app.post("/api/power/confirm", dependencies=[Depends(token_check)])
    def confirm(body: Control, device_id=Depends(token_check)):
        if body.action not in ACTIONS:
            raise DeskError("invalid_action", "电源动作无效")
        return auth.confirm(body.action, device_id)

    @app.post("/api/power", dependencies=[Depends(token_check)])
    async def power(body: Confirmation, device_id=Depends(token_check)):
        if body.action not in ACTIONS:
            raise DeskError("invalid_action", "电源动作无效")
        auth.consume(body.nonce, body.action, device_id)
        if demo:
            return {"ok": True, "demo": True, "message": "演示模式：没有执行电源操作"}
        asyncio.get_running_loop().call_later(0.4, lambda: asyncio.create_task(asyncio.to_thread(modules["power"].execute, body.action)))
        return {"ok": True, "message": "指令已发送"}

    @app.get("/api/devices", dependencies=[Depends(token_check)])
    def devices():
        return {"devices": auth.list_devices()}

    @app.delete("/api/devices/{device_id}", dependencies=[Depends(token_check)])
    def revoke(device_id: str):
        auth.revoke(device_id)
        return {"ok": True}

    @app.websocket("/ws")
    async def ws(socket: WebSocket):
        ws_hostname = urlsplit("//" + socket.headers.get("host", "")).hostname
        if ws_hostname not in {"localhost", "testserver", __import__("socket").gethostname().lower(), *local_addresses()} or not safe_peer(socket.client.host) or not origin_ok(socket.headers.get("origin"), socket.headers.get("host", "")):
            await socket.close(code=1008)
            return
        await socket.accept()
        try:
            first = await asyncio.wait_for(socket.receive_json(), timeout=5)
            if not isinstance(first, dict) or first.get("type") != "auth":
                raise DeskError("invalid_token", "请先认证", 401)
            await hub.join(socket, first.get("token", ""))
            await socket.send_json({"type": "ready"})
            await hub.send(socket, {"type": "state", "ts": int(time.time() * 1000), "system": state.get("system", {}), "audio": state.get("audio", {}), "media": state.get("media", {}), "apps": state.get("apps", {})})
            while True:
                data = await asyncio.wait_for(socket.receive_json(), timeout=45)
                if isinstance(data, dict) and data.get("type") == "ping":
                    await hub.send(socket, {"type": "pong"})
        except DeskError as exc:
            await socket.close(code=1013 if exc.status == 429 else 1008)
        except (WebSocketDisconnect, asyncio.TimeoutError):
            with contextlib.suppress(Exception):
                await socket.close(code=1001)
        except (ValueError, TypeError):
            with contextlib.suppress(Exception):
                await socket.close(code=1008)
        finally:
            hub.leave(socket)

    @app.get("/")
    def index():
        return FileResponse(ROOT / "web" / "index.html")

    app.mount("/", StaticFiles(directory=ROOT / "web"), name="web")
    return app


def run():
    parser = argparse.ArgumentParser(description="DeskTouch local PC control panel")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--background", action="store_true")
    parser.add_argument("--no-autostart", action="store_true")
    parser.add_argument("--test-ready-file", type=Path, default=None, help="Demo-only local test handshake")
    options = parser.parse_args()
    if options.test_ready_file and not options.demo:
        parser.error("--test-ready-file requires --demo")
    app = create_app(options.data_dir, options.demo)
    logs = app.state.data_dir.parent / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    handlers = [TimedRotatingFileHandler(logs / "desktouch.log", when="midnight", backupCount=7, encoding="utf-8")]
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, handlers=handlers, format="%(asctime)s %(levelname)s %(message)s")
    settings = app.state.config.snapshot()["server"]
    host = options.host or settings["host"]
    port = options.port or settings["port"]
    if host == "lan":
        from .network import pick
        chosen, rows = pick(settings.get("preferred_host") or None)
        if not chosen:
            raise SystemExit("No usable private LAN IPv4 found. Connect Wi-Fi, then retry or pass --host <ip>.")
        host = chosen
        print("Adapters: " + ", ".join(row["address"] + " (" + row["interface"] + ")" for row in rows), flush=True)
    try:
        addr = ipaddress.ip_address(host)
        if not addr.is_loopback and not (str(addr).startswith("10.") or str(addr).startswith("192.168.") or ipaddress.ip_address("172.16.0.0") <= addr <= ipaddress.ip_address("172.31.255.255")):
            raise ValueError
    except (ValueError, TypeError):
        raise SystemExit("Only loopback/private LAN IPv4 binding is supported; 0.0.0.0 is disabled.")
    print("\nDeskTouch " + __version__ + (" [DEMO: no PC control]" if options.demo else ""), flush=True)
    print("Open: http://" + host + ":" + str(port), flush=True)
    print("Pairing code (valid 10 minutes): " + app.state.auth.code, flush=True)
    print("Existing paired devices remain valid. Restart to obtain a new pairing code.\n", flush=True)
    import qrcode
    qr = qrcode.QRCode(border=1)
    qr.add_data("http://" + host + ":" + str(port))
    qr.make()
    qr.make_image().save(app.state.data_dir / "connection-qr.png")
    try:
        if sys.stdout is not None:
            qr.print_ascii(invert=True)
    except UnicodeEncodeError:
        print("QR image saved as data/connection-qr.png", flush=True)
    import uvicorn
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, access_log=False, ws_max_size=4096, proxy_headers=False, log_config=None, use_colors=False))
    if options.test_ready_file:
        ready = options.test_ready_file.resolve()
        if not ready.is_relative_to(app.state.data_dir.resolve()) or ready.name != "ready.json":
            raise SystemExit("Test handshake must be inside the demo data directory")
        import threading
        from .common import atomic_json
        def test_handshake():
            while not server.started and not server.should_exit:
                time.sleep(0.05)
            if server.started:
                atomic_json(ready, {"code": app.state.auth.code, "demo": True, "pid": os.getpid()})
        threading.Thread(target=test_handshake, daemon=True).start()
    server.run()


if __name__ == "__main__":
    run()
