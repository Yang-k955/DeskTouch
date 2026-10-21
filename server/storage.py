"""Stable per-user state. Migration copies only known files; originals stay intact."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .common import DeskError, atomic_json

SOURCE_ROOT = Path(__file__).resolve().parents[1]
STATE_FILES = ("config.json", "state.json")


def stable_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Local")
    return Path(base) / "DeskTouch" / "data"


def import_legacy(source: Path, destination: Path):
    """Non-destructive first-run import. Refuse to overwrite any existing state."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination:
        return []
    if any((destination / name).exists() for name in STATE_FILES):
        raise DeskError("state_exists", "当前数据目录已有配置或配对记录，不会覆盖。请先保留现有数据再选择其他目录。", 409)
    rows = {}
    for name in STATE_FILES:
        path = source / name
        if not path.is_file():
            continue
        if path.is_symlink() or path.stat().st_size > 4 * 1024 * 1024:
            raise DeskError("invalid_legacy", "旧版状态文件无效或过大")
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        if name == "config.json":
            from .config import validate
            validate(value)
        elif not isinstance(value, dict) or not isinstance(value.get("devices"), list):
            raise DeskError("invalid_legacy", "旧版设备记录格式错误")
        rows[name] = value
    if not rows:
        raise DeskError("missing_legacy", "所选目录没有 config.json 或 state.json", 404)
    # Validate every source before writing anything. Never import caches, logs or executables.
    for name, value in rows.items():
        atomic_json(destination / name, value)
    atomic_json(destination / "migration.json", {"source": str(source), "files": list(rows), "originals_preserved": True})
    return list(rows)


def resolve_data_dir(data_dir=None, demo=False) -> Path:
    explicit = data_dir or os.environ.get("DESKTOUCH_DATA_DIR")
    if not explicit and not demo:
        selection = stable_data_dir().parent / "location.json"
        if selection.is_file():
            value = json.loads(selection.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or not isinstance(value.get("data_dir"), str) or not value["data_dir"]:
                raise DeskError("invalid_location", "旧版数据目录选择无效，请检查 location.json")
            explicit = value["data_dir"]
            if not Path(explicit).is_dir():
                raise DeskError("missing_location", "之前选择的数据目录已不存在，请恢复目录或修改 location.json；不会自动重置配对")
    result = Path(explicit).expanduser().resolve() if explicit else stable_data_dir().resolve()
    if demo:
        result = result if result.name == "demo-data" else result / "demo-data"
    elif not explicit and not any((result / name).exists() for name in STATE_FILES):
        legacy = Path(sys.executable).resolve().parent / "data" if getattr(sys, "frozen", False) else SOURCE_ROOT / "data"
        if legacy != result and any((legacy / name).is_file() for name in STATE_FILES):
            import_legacy(legacy, result)
    result.mkdir(parents=True, exist_ok=True)
    return result
