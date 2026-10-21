from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from ctypes import POINTER, cast

from .common import DeskError

try:
    import pythoncom
except ImportError:
    pythoncom = None


class Audio:
    def __init__(self):
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="desktouch-audio")

    def _endpoint(self):
        # 在 worker 内导入，避免 comtypes 在请求线程隐式初始化 COM。
        first_import = "comtypes" not in sys.modules
        import comtypes
        # comtypes 首次导入额外初始化一次，立即平衡；当前调用自己的 COM 初始化仍有效。
        if first_import:
            comtypes.CoUninitialize()
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        device = AudioUtilities.GetSpeakers()
        if device is None:
            raise RuntimeError("没有默认音频输出设备")
        if hasattr(device, "EndpointVolume"):
            volume = device.EndpointVolume
        else:
            volume = cast(device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None), POINTER(IAudioEndpointVolume))
        return device, volume

    def _operation(self, action, value):
        initialized = False
        device = endpoint = None
        try:
            if pythoncom is None:
                raise RuntimeError("Windows Core Audio COM 不可用")
            pythoncom.CoInitialize()
            initialized = True
            device, endpoint = self._endpoint()
            if action == "volume":
                endpoint.SetMasterVolumeLevelScalar(value / 100, None)
            elif action == "mute":
                endpoint.SetMute(value, None)
            return {"available": True, "volume": round(endpoint.GetMasterVolumeLevelScalar() * 100), "muted": bool(endpoint.GetMute()), "device": getattr(device, "FriendlyName", None) or None}
        except Exception as exc:
            return {"available": False, "volume": None, "muted": None, "device": None, "message": "音频不可用：" + str(exc)}
        finally:
            endpoint = device = None
            if initialized:
                pythoncom.CoUninitialize()

    def snapshot(self):
        return self._worker.submit(self._operation, "read", None).result()

    def set_volume(self, value: int):
        if type(value) is not int or not 0 <= value <= 100:
            raise DeskError("invalid_volume", "音量必须为 0–100 的整数")
        return self._worker.submit(self._operation, "volume", value).result()

    def set_mute(self, value: bool):
        if type(value) is not bool:
            raise DeskError("invalid_mute", "静音状态必须为布尔值")
        return self._worker.submit(self._operation, "mute", value).result()

    def close(self):
        self._worker.shutdown(wait=True)
