from __future__ import annotations

import copy
import socket
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor

import psutil

try:
    import win32gui
    import win32process
except ImportError:
    win32gui = win32process = None


class Monitor:
    def __init__(self):
        self._worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="desktouch-monitor")
        self._lock = threading.RLock()
        self._history = deque(maxlen=60)
        self._last = None
        self._last_sample = None
        self._net = None
        self._net_at = None
        self._disks = []
        self._disks_at = None
        self._worker.submit(self._prime).result()

    def _prime(self):
        psutil.cpu_percent(interval=None)
        self._net = psutil.net_io_counters()
        self._net_at = time.monotonic()

    def _foreground(self):
        if win32gui is None:
            return {"process": None, "title": None}
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return {"process": None, "title": None}
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return {"process": psutil.Process(pid).name(), "title": win32gui.GetWindowText(hwnd)}
        except (psutil.Error, OSError, RuntimeError):
            return {"process": None, "title": None}
        except Exception:
            return {"process": None, "title": None}

    def _read_disks(self):
        disks, seen = [], set()
        for part in psutil.disk_partitions(all=False):
            if part.mountpoint in seen or "cdrom" in part.opts or not part.fstype:
                continue
            seen.add(part.mountpoint)
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({"mount": part.mountpoint, "used": usage.used, "total": usage.total, "percent": usage.percent})
            except (OSError, psutil.Error):
                continue
        return disks

    def _sample(self):
        now = time.monotonic()
        with self._lock:
            if self._last is not None and now - self._last_sample < 1:
                return copy.deepcopy(self._last)
            cpu = psutil.cpu_percent(interval=None)
            self._history.append(cpu)
            memory = psutil.virtual_memory()
            counters = psutil.net_io_counters()
            elapsed = now - self._net_at
            network = {"up": 0.0, "down": 0.0}
            if counters is not None and self._net is not None and elapsed > 0:
                network = {"up": max(0, counters.bytes_sent - self._net.bytes_sent) / elapsed, "down": max(0, counters.bytes_recv - self._net.bytes_recv) / elapsed}
            self._net, self._net_at = counters, now
            if self._disks_at is None or now - self._disks_at >= 15:
                self._disks = self._read_disks()
                self._disks_at = now
            try:
                battery = psutil.sensors_battery()
            except (AttributeError, OSError, psutil.Error):
                battery = None
            self._last = {"cpu": {"percent": cpu, "cores": psutil.cpu_count() or 1, "history": list(self._history)}, "memory": {"used": memory.used, "total": memory.total, "percent": memory.percent}, "disks": self._disks, "network": network, "uptime": max(0, time.time() - psutil.boot_time()), "hostname": socket.gethostname(), "foreground": self._foreground(), "battery": {"percent": battery.percent, "charging": bool(battery.power_plugged)} if battery else None}
            self._last_sample = now
            return copy.deepcopy(self._last)

    def snapshot(self):
        return self._worker.submit(self._sample).result()

    def close(self):
        self._worker.shutdown(wait=True)
