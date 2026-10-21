from __future__ import annotations

import hashlib
import json
import secrets
import threading
import time
from pathlib import Path

from .common import DeskError, atomic_json


class Auth:
    """Pairing requires a short-lived PC-only code; disk stores token hashes only."""
    def __init__(self, data_dir: Path):
        self.path = data_dir / "state.json"
        self.lock = threading.RLock()
        self.attempts = {}
        self.nonces = {}
        self.devices = []
        if self.path.exists():
            self.devices = json.loads(self.path.read_text(encoding="utf-8"))["devices"]
            changed = False
            for device in self.devices:
                expiry = device.get("expires_at")
                # Upgrade still-valid 1.0 credentials, never resurrect expired/revoked tokens.
                if isinstance(expiry, (int, float)) and expiry > time.time() * 1000:
                    device["expires_at"] = None
                    changed = True
            if changed:
                atomic_json(self.path, {"devices": self.devices})
        self.rotate()

    def rotate(self):
        with self.lock:
            self.code = str(secrets.randbelow(1000000)).zfill(6)
            self.code_until = time.monotonic() + 600
        return self.code

    @staticmethod
    def hashed(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def pair(self, code, name, ip):
        with self.lock:
            now = time.monotonic()
            count, until = self.attempts.get(ip, (0, 0))
            if count >= 3 and now < until:
                raise DeskError("rate_limited", "连续失败，请稍后重试", 429)
            if now >= until:
                count = 0
            if not isinstance(code, str) or now > self.code_until or not secrets.compare_digest(code, self.code):
                self.attempts[ip] = (count + 1, now + 60)
                raise DeskError("invalid_code", "配对码错误或已过期，请查看电脑启动窗口", 401)
            self.attempts.pop(ip, None)
            token = "dt_" + secrets.token_urlsafe(32)
            expires = None  # Trusted devices remain paired until explicitly revoked.
            self.devices.append({"id": secrets.token_hex(8), "name": name[:64], "token_hash": self.hashed(token), "expires_at": expires, "paired_at": int(time.time() * 1000)})
            self.devices = self.devices[-50:]
            atomic_json(self.path, {"devices": self.devices})
            return {"ok": True, "token": token, "expires_at": expires}

    def check(self, token):
        if not isinstance(token, str) or not token or len(token) > 200:
            raise DeskError("invalid_token", "请先配对电脑", 401)
        hashed = self.hashed(token)
        with self.lock:
            for device in self.devices:
                if secrets.compare_digest(device["token_hash"], hashed) and (device.get("expires_at") is None or device["expires_at"] > time.time() * 1000):
                    return device["id"]
        raise DeskError("invalid_token", "配对已失效，请重新配对", 401)

    def list_devices(self):
        with self.lock:
            return [{k: v for k, v in d.items() if k != "token_hash"} for d in self.devices]

    def revoke(self, device_id):
        with self.lock:
            self.devices = [d for d in self.devices if d["id"] != device_id]
            atomic_json(self.path, {"devices": self.devices})

    def confirm(self, action, device_id):
        with self.lock:
            now = time.monotonic()
            self.nonces = {n: row for n, row in self.nonces.items() if row[2] > now}
            nonce = secrets.token_urlsafe(24)
            self.nonces[nonce] = (action, device_id, now + 30, now)
        return {"nonce": nonce, "expires_in": 30, "min_hold_ms": 1500}

    def consume(self, nonce, action, device_id):
        with self.lock:
            row = self.nonces.get(nonce)
            if row is None or row[:2] != (action, device_id) or time.monotonic() > row[2]:
                raise DeskError("invalid_confirmation", "确认已过期，请重新操作", 409)
            if time.monotonic() - row[3] < 1.5:
                raise DeskError("hold_required", "请长按确认按钮至少 1.5 秒", 409)
            del self.nonces[nonce]
