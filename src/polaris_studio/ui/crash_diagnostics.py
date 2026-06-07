from __future__ import annotations

import os
import sys
from typing import Any

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    EXCEPTION_ACCESS_VIOLATION = 0xC0000005
    EXCEPTION_CONTINUE_SEARCH = 0

    class EXCEPTION_POINTERS(ctypes.Structure):
        _fields_ = [
            ("ExceptionRecord", wintypes.LPVOID),
            ("ContextRecord", wintypes.LPVOID),
        ]

    EXCEPTION_HANDLER: Any = ctypes.WINFUNCTYPE(wintypes.DWORD, ctypes.POINTER(EXCEPTION_POINTERS))

    def _exception_handler(exception_info: ctypes.POINTER(EXCEPTION_POINTERS)) -> int:
        try:
            crash_log = os.path.join(os.getcwd(), f"crash_{os.getpid()}.log")
            with open(crash_log, "w") as f:
                f.write("STATUS_ACCESS_VIOLATION (0xC0000005) detected\n")
                f.write(f"PID: {os.getpid()}\n")
                f.write(f"Python: {sys.version}\n")
                f.write("See event log for full stack trace\n")
        except Exception:
            pass
        return EXCEPTION_CONTINUE_SEARCH

    def install_crash_handler() -> None:
        kernel32 = ctypes.windll.kernel32
        handler = EXCEPTION_HANDLER(_exception_handler)
        kernel32.SetUnhandledExceptionFilter(handler)

else:

    def install_crash_handler() -> None:
        pass
