"""Original local SVG glyph collection. No remote assets or user SVG execution."""
from __future__ import annotations
from .common import DeskError

# id: (Chinese label, pastel background, saturated ink, 24-unit paths)
GLYPHS = {
    "desktop": ("桌面", "#e5edff", "#3465d9", "M3 4h18v13H3z M8 21h8 M12 17v4"),
    "browser": ("浏览器", "#e2f4f0", "#168773", "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0 M3 12h18 M12 3c-5 5-5 13 0 18 M12 3c5 5 5 13 0 18"),
    "editor": ("编辑器", "#eee8ff", "#7550c9", "M4 4h16v16H4z M8 8h8 M8 12h5 M8 16h7"),
    "terminal": ("终端", "#e8edf4", "#405b7b", "M3 4h18v16H3z M7 9l4 3-4 3 M13 16h4"),
    "folder": ("文件夹", "#fff2d8", "#b77e16", "M3 7V4h6l3 3h9v13H3z M3 10h18"),
    "music": ("音乐", "#fce5ee", "#cc4b7f", "M9 18V5l11-2v13 M9 7l11-2 M9 18a3 3 0 1 1-3-3h3 M20 16a3 3 0 1 1-3-3h3"),
    "video": ("视频", "#ffe9e0", "#c96f43", "M3 5h18v14H3z M10 9l5 3-5 3z"),
    "game": ("游戏", "#e8e4ff", "#6753cb", "M7 7h10l4 11c1 3-3 4-5 0H8c-2 4-6 3-5 0z M6 12h6 M9 9v6 M16 11h.01 M18 14h.01"),
    "chat": ("聊天", "#e3f5e9", "#3a965d", "M3 4h18v13H9l-6 4z M7 9h10 M7 13h7"),
    "mail": ("邮件", "#e6efff", "#4377cf", "M3 5h18v14H3z M3 6l9 7 9-7"),
    "document": ("文档", "#e4edff", "#3868ce", "M5 3h9l5 5v13H5z M14 3v6h5 M8 13h8 M8 17h6"),
    "sheet": ("表格", "#e1f4e7", "#348857", "M4 3h16v18H4z M4 9h16 M4 15h16 M10 9v12"),
    "slides": ("演示", "#ffecdf", "#c77c3d", "M3 4h18v13H3z M12 17v4 M7 21l5-4 5 4 M7 12V9 M12 12V7 M17 12v-2"),
    "photo": ("图片", "#f2e5ff", "#9851b3", "M3 4h18v16H3z M3 17l6-7 4 4 3-3 5 6 M17 7h.01"),
    "settings": ("设置", "#e9eef4", "#60728a", "M9 3h6l1 4 4 2v6l-4 2-1 4H9l-1-4-4-2V9l4-2z M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0"),
    "cloud": ("云盘", "#e0f2ff", "#3183b7", "M6 18a5 5 0 0 1-1-10 7 7 0 0 1 13-1 5 5 0 0 1 1 11z"),
    "code": ("开发", "#e5eaff", "#5262c7", "M8 6l-6 6 6 6 M16 6l6 6-6 6 M14 3l-4 18"),
    "tools": ("工具", "#e4f1f2", "#418b91", "M14 3a6 6 0 0 0-7 8l-5 6 5 5 6-6a6 6 0 0 0 8-7l-4 4-4-4z"),
    "download": ("下载", "#e8f3df", "#6f9336", "M12 3v12 M7 10l5 5 5-5 M3 16v5h18v-5"),
    "star": ("收藏", "#fff2d4", "#bc8a20", "M12 2l3 7 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z"),
}


def library():
    return [{"id": key, "name": row[0], "url": "/api/icon-library/" + key + ".svg"} for key, row in GLYPHS.items()]


def svg(icon_id: str) -> str:
    row = GLYPHS.get(icon_id)
    if not row:
        raise DeskError("unknown_icon", "默认图标不存在", 404)
    label, background, ink, path = row
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">'
            '<title>' + label + '</title><rect width="256" height="256" rx="60" fill="' + background + '"/>'
            '<path d="' + path + '" transform="translate(44 44) scale(7)" fill="none" stroke="' + ink +
            '" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
