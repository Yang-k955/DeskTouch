"""源码和无控制台打包入口，默认启动 Windows 桌面托盘。"""
import sys
from pathlib import Path

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    from server.desktop import run_desktop
    return run_desktop()


if __name__ == "__main__":
    raise SystemExit(main())
