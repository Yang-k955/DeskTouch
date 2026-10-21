from __future__ import annotations

import asyncio
import base64
from datetime import timedelta

from .common import DeskError

try:
    from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as SessionManager
    from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
    from winrt.windows.storage.streams import Buffer, DataReader, InputStreamOptions
    import pythoncom
except ImportError:
    SessionManager = PlaybackStatus = Buffer = DataReader = InputStreamOptions = pythoncom = None

try:
    import win32api
    import win32con
except ImportError:
    win32api = win32con = None

MAX_COVER = 512 * 1024
ACTIONS = {"play_pause": "try_toggle_play_pause_async", "play": "try_play_async", "pause": "try_pause_async", "next": "try_skip_next_async", "previous": "try_skip_previous_async"}


def seconds(value):
    if isinstance(value, timedelta):
        return value.total_seconds()
    return float(value) / 10_000_000 if isinstance(value, (int, float)) else 0.0


def empty(available, message=None):
    result = {"available": available, "active": False, "title": None, "artist": None, "album": None, "playing": None, "player": None, "position": None, "duration": None}
    if message:
        result["message"] = message
    return result


class Media:
    async def _session(self):
        if SessionManager is None:
            raise RuntimeError("winrt.windows.media.control 不可用")
        manager = await SessionManager.request_async()
        return manager.get_current_session()

    async def _cover(self, thumbnail):
        if thumbnail is None:
            return None
        stream = reader = None
        try:
            stream = await thumbnail.open_read_async()
            size = stream.size
            mime = stream.content_type or ""
            if not 0 < size <= MAX_COVER or mime not in {"image/png", "image/jpeg", "image/webp", "image/gif", "image/bmp"}:
                return None
            buffer = await stream.read_async(Buffer(size), size, InputStreamOptions.NONE)
            if buffer.length != size:
                return None
            reader = DataReader.from_buffer(buffer)
            data = bytearray(size)
            reader.read_bytes(data)
            return "data:" + mime + ";base64," + base64.b64encode(data).decode("ascii")
        except Exception:
            return None
        finally:
            try:
                if reader is not None:
                    reader.close()
            finally:
                if stream is not None:
                    stream.close()

    async def snapshot(self):
        initialized = False
        session = properties = timeline = playback = None
        try:
            if pythoncom is not None:
                pythoncom.CoInitialize()
                initialized = True
            session = await asyncio.wait_for(self._session(), timeout=3)
            if session is None:
                return empty(True)
            properties = await asyncio.wait_for(session.try_get_media_properties_async(), timeout=3)
            if properties is None:
                raise RuntimeError("播放器未提供媒体属性")
            playback = session.get_playback_info()
            timeline = session.get_timeline_properties()
            start, end = seconds(timeline.start_time), seconds(timeline.end_time)
            result = {"available": True, "active": True, "title": properties.title or "", "artist": properties.artist or "", "album": properties.album_title or "", "playing": playback.playback_status == PlaybackStatus.PLAYING, "player": session.source_app_user_model_id, "position": max(0, seconds(timeline.position) - start), "duration": max(0, end - start)}
            try:
                cover = await asyncio.wait_for(self._cover(properties.thumbnail), timeout=3)
            except (TimeoutError, OSError):
                cover = None
            if cover:
                result["cover"] = cover
            return result
        except Exception as exc:
            return empty(False, "媒体信息不可用：" + (str(exc) or type(exc).__name__))
        finally:
            session = properties = timeline = playback = None
            if initialized:
                pythoncom.CoUninitialize()

    def _media_key(self, action):
        keys = {"play_pause": 0xB3, "next": 0xB0, "previous": 0xB1}
        if action not in keys or win32api is None:
            raise DeskError("module_unavailable", "媒体会话不可用，且无法发送此媒体键", 503)
        win32api.keybd_event(keys[action], 0, 0, 0)
        win32api.keybd_event(keys[action], 0, win32con.KEYEVENTF_KEYUP, 0)

    async def control(self, action):
        if not isinstance(action, str) or action not in ACTIONS:
            raise DeskError("invalid_media_action", "不支持的媒体操作")
        initialized = False
        session = None
        reason = "没有活跃媒体会话"
        try:
            if pythoncom is not None:
                pythoncom.CoInitialize()
                initialized = True
            session = await asyncio.wait_for(self._session(), timeout=3)
            if session is not None:
                ok = bool(await asyncio.wait_for(getattr(session, ACTIONS[action])(), timeout=3))
                return {"ok": ok, "mode": "smtc", **({} if ok else {"message": "播放器拒绝此操作"})}
        except Exception as exc:
            reason = str(exc) or type(exc).__name__
        finally:
            session = None
            if initialized:
                pythoncom.CoUninitialize()
        try:
            self._media_key(action)
        except DeskError:
            raise
        except Exception as exc:
            raise DeskError("media_control_failed", "媒体键发送失败：" + str(exc), 503) from exc
        return {"ok": True, "mode": "media_keys", "message": "已发送媒体键，无法确认播放器状态：" + reason}
