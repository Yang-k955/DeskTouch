"""Bounded local file browser for choosing an executable on the PC from the tablet."""
from __future__ import annotations

import ntpath
import os
import string
from pathlib import Path

from .common import DeskError

LAUNCHABLE = {".exe", ".lnk", ".cmd", ".bat"}
MAX_ENTRIES = 500
SKIP_NAMES = {"$recycle.bin", "system volume information", "recovery", "config.msi"}


def drives():
    rows = []
    for letter in string.ascii_uppercase:
        root = letter + ":\\"
        if os.path.exists(root):
            rows.append({"name": letter + ":", "path": root})
    return rows


def _absolute(value):
    if not isinstance(value, str) or not value or "\x00" in value or len(value) > 500:
        raise DeskError("invalid_path", "路径无效", 400)
    expanded = os.path.expandvars(value.strip().strip('"'))
    if expanded.startswith("\\\\") or expanded.startswith("//"):
        raise DeskError("invalid_path", "不支持网络路径", 400)
    normalized = ntpath.normpath(expanded)
    if not ntpath.isabs(normalized) or not ntpath.splitdrive(normalized)[0]:
        raise DeskError("invalid_path", "请使用带盘符的完整路径", 400)
    return normalized


def listing(value=""):
    if not value:
        return {"path": "", "parent": None, "entries": [{"name": row["name"], "path": row["path"], "type": "dir"} for row in drives()]}
    target = Path(_absolute(value))
    if target.is_symlink():
        raise DeskError("invalid_path", "不浏览符号链接目录", 400)
    if not target.exists():
        raise DeskError("path_missing", "目录不存在", 404)
    if not target.is_dir():
        raise DeskError("not_a_directory", "这不是文件夹", 400)
    entries = []
    try:
        children = sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.casefold()))
    except PermissionError as exc:
        raise DeskError("access_denied", "没有权限读取该目录", 403) from exc
    except OSError as exc:
        raise DeskError("access_denied", "无法读取该目录：" + str(exc), 403) from exc
    for child in children:
        if len(entries) >= MAX_ENTRIES:
            break
        name = child.name
        if name.casefold() in SKIP_NAMES or name.startswith("$"):
            continue
        try:
            if child.is_symlink():
                continue
            if child.is_dir():
                entries.append({"name": name, "path": str(child), "type": "dir"})
            elif child.suffix.casefold() in LAUNCHABLE and child.is_file():
                entries.append({"name": name, "path": str(child), "type": "file"})
        except OSError:
            continue
    parent = str(target.parent) if target.parent != target else None
    return {"path": str(target), "parent": parent, "entries": entries, "truncated": len(entries) >= MAX_ENTRIES}


def validate_launch_target(value):
    """Classify a user-chosen target. Only absolute local executables/shortcuts/folders."""
    from .launcher import valid_uri

    if not isinstance(value, str) or not value.strip() or "\x00" in value or len(value) > 500:
        raise DeskError("invalid_path", "启动地址无效", 400)
    candidate = value.strip().strip('"')
    if not ntpath.splitdrive(candidate)[0]:
        if valid_uri(candidate):
            return {"type": "uri", "path": candidate}
        raise DeskError("invalid_path", "请使用带盘符的完整路径，或受支持的协议链接", 400)
    path = _absolute(candidate)
    target = Path(path)
    if not target.exists():
        raise DeskError("path_missing", "找不到该文件或文件夹：" + path, 404)
    if target.is_dir():
        return {"type": "shell", "path": path}
    suffix = target.suffix.casefold()
    if suffix in {".lnk", ".url"}:
        return {"type": "shell", "path": path}
    if suffix == ".exe":
        return {"type": "exe", "path": path}
    if suffix in {".cmd", ".bat"}:
        return {"type": "cmd", "path": path}
    raise DeskError("invalid_path", "只支持 exe、快捷方式、批处理、文件夹或允许的协议链接", 400)
