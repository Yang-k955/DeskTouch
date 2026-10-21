from __future__ import annotations

import os
import sys
import tempfile
import threading
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .common import DeskError, digest

try:
    import win32con
    import win32gui
    import win32ui
    from win32com.shell import shell, shellcon
except ImportError:
    win32con = win32gui = win32ui = shell = shellcon = None

PROJECT_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]


class Icons:
    def __init__(self, data_dir):
        self.directory = (Path(data_dir) / "icons").resolve()
        # Cache lives beneath the server-selected data directory, never a browser path.
        if self.directory.parent != Path(data_dir).resolve():
            raise DeskError("invalid_icon_cache", "图标缓存不能通过链接指向数据目录之外")
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _extract(self, target):
        path, index = target, 0
        if "," in target:
            candidate, suffix = target.rsplit(",", 1)
            try:
                index = int(suffix)
                path = candidate
            except ValueError:
                pass
        if win32gui is None or not Path(path).is_file():
            return None
        handles = []
        dc = memory = bitmap = previous = None
        try:
            if path.lower().endswith(".lnk"):
                _, info = shell.SHGetFileInfo(path, 0, shellcon.SHGFI_ICON | shellcon.SHGFI_LARGEICON)
                if info[0]:
                    handles.append(info[0])
            else:
                # Ask Windows for the actual 256px resource before falling back to legacy icons.
                try:
                    import ctypes
                    from ctypes import wintypes
                    extract = ctypes.WinDLL("shell32").SHDefExtractIconW
                    extract.argtypes = [wintypes.LPCWSTR, ctypes.c_int, wintypes.UINT, ctypes.POINTER(wintypes.HICON), ctypes.POINTER(wintypes.HICON), wintypes.UINT]
                    extract.restype = ctypes.c_long
                    big, little = wintypes.HICON(), wintypes.HICON()
                    result = extract(path, index, 0, ctypes.byref(big), ctypes.byref(little), 256 | (32 << 16))
                    if result == 0:
                        handles.extend(h for h in (big.value, little.value) if h)
                except (OSError, AttributeError):
                    pass
                if not handles:
                    large, small = win32gui.ExtractIconEx(path, index)
                    handles.extend(large)
                    handles.extend(small)
            if not handles:
                return None
            # 创建自有 DC，使用 DeleteDC 释放；避免对 GetDC 借用句柄错误调用 DeleteDC。
            dc = win32ui.CreateDCFromHandle(win32gui.CreateDC("DISPLAY", None, None))
            memory = dc.CreateCompatibleDC()
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(dc, 256, 256)
            previous = memory.SelectObject(bitmap)
            memory.FillSolidRect((0, 0, 256, 256), 0)
            win32gui.DrawIconEx(memory.GetSafeHdc(), 0, 0, handles[0], 256, 256, 0, None, win32con.DI_NORMAL)
            image = Image.frombuffer("RGBA", (256, 256), bitmap.GetBitmapBits(True), "raw", "BGRA", 0, 1).copy()
            if not image.getchannel("A").getbbox():
                image.putalpha(255)
            return image
        finally:
            try:
                if memory and previous:
                    memory.SelectObject(previous)
                if bitmap:
                    win32gui.DeleteObject(bitmap.GetHandle())
                if memory:
                    memory.DeleteDC()
                if dc:
                    dc.DeleteDC()
            finally:
                for handle in set(handles):
                    if handle:
                        try:
                            win32gui.DestroyIcon(handle)
                        except Exception:
                            pass

    def _placeholder(self, name):
        color = tuple(55 + int(digest(name)[index:index + 2], 16) % 130 for index in (0, 2, 4))
        image = Image.new("RGBA", (256, 256), (*color, 255))
        font = None
        for filename in ("msyh.ttc", "seguiemj.ttf", "arial.ttf"):
            try:
                font = ImageFont.truetype(str(Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / filename), 128)
                break
            except OSError:
                continue
        font = font or ImageFont.load_default(size=128)
        ImageDraw.Draw(image).text((128, 128), (name.strip() or "?")[0].upper(), fill="white", font=font, anchor="mm")
        return image

    def get(self, key: str, name: str, target: str) -> Path:
        if not all(isinstance(value, str) for value in (key, name, target)):
            raise DeskError("invalid_icon", "图标参数必须为字符串")
        path = self.directory / (digest("hd-v2\0" + key + "\0" + name + "\0" + target) + ".png")
        with self._lock:
            if path.is_file():
                try:
                    with Image.open(path) as cached:
                        cached.verify()
                    return path
                except (OSError, ValueError):
                    pass
            try:
                image = self._extract(target)
            except Exception:
                image = None
            if image is None:
                image = self._placeholder(name)
            fd, tmp = tempfile.mkstemp(prefix=path.stem + ".", suffix=".tmp", dir=self.directory)
            os.close(fd)
            try:
                image.save(tmp, format="PNG")
                os.replace(tmp, path)
            finally:
                image.close()
                if os.path.exists(tmp):
                    os.unlink(tmp)
        return path
