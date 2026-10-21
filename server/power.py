from __future__ import annotations

import ctypes
import os
import subprocess

from .common import DeskError

try:
    import win32api
    import win32con
    import win32security
except ImportError:
    win32api = win32con = win32security = None


class Power:
    def _lock(self):
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.LockWorkStation.argtypes = []
        user32.LockWorkStation.restype = ctypes.c_bool
        if not user32.LockWorkStation():
            raise ctypes.WinError(ctypes.get_last_error())

    def _display_off(self):
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.SendMessageTimeoutW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_size_t)]
        user32.SendMessageTimeoutW.restype = ctypes.c_ssize_t
        result = ctypes.c_size_t()
        if not user32.SendMessageTimeoutW(0xFFFF, 0x0112, 0xF170, 2, 0x0002, 1000, ctypes.byref(result)):
            raise ctypes.WinError(ctypes.get_last_error())

    def _sleep(self):
        if win32security is None:
            raise RuntimeError("Windows 电源 API 不可用")
        token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY)
        previous = None
        try:
            privilege = win32security.LookupPrivilegeValue(None, "SeShutdownPrivilege")
            previous = win32security.AdjustTokenPrivileges(token, False, [(privilege, win32con.SE_PRIVILEGE_ENABLED)])
            if win32api.GetLastError() == 1300:
                raise RuntimeError("未获得睡眠所需的电源权限")
            api = ctypes.WinDLL("powrprof", use_last_error=True)
            api.SetSuspendState.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, ctypes.c_ubyte]
            api.SetSuspendState.restype = ctypes.c_ubyte
            if not api.SetSuspendState(False, False, False):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            try:
                if previous is not None:
                    win32security.AdjustTokenPrivileges(token, False, previous)
            finally:
                token.Close()

    def _shutdown(self, restart):
        target = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "System32", "shutdown.exe")
        # 不使用 /f 强制关闭应用，不使用 shell 拼接命令。
        subprocess.run([target, "/r" if restart else "/s", "/t", "0"], shell=False, check=True, capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    def execute(self, action):
        actions = {"lock": self._lock, "display_off": self._display_off, "sleep": self._sleep, "restart": lambda: self._shutdown(True), "shutdown": lambda: self._shutdown(False)}
        if not isinstance(action, str) or action not in actions:
            raise DeskError("invalid_power_action", "不支持的电源操作")
        try:
            actions[action]()
            return {"ok": True}
        except DeskError:
            raise
        except Exception as exc:
            raise DeskError("power_failed", "电源操作失败：" + str(exc), 500) from exc
