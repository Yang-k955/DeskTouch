from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path


class DeskError(Exception):
    def __init__(self, error: str, message: str, status: int = 400):
        super().__init__(message)
        self.error, self.message, self.status = error, message, status


def atomic_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(data, out, ensure_ascii=False, indent=2)
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def identity(app: dict) -> str:
    kind = app.get("type", app.get("suggested_type", "exe"))
    path = app.get("path", app.get("target", ""))
    args = app.get("args", [])
    return json.dumps([kind, os.path.normcase(path).casefold(), args], ensure_ascii=False, sort_keys=True)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]
