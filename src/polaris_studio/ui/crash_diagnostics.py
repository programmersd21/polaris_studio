from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime
from typing import Any

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    EXCEPTION_ACCESS_VIOLATION = 0xC0000005
    EXCEPTION_CONTINUE_SEARCH = 0
    EXCEPTION_EXECUTE_HANDLER = 1

    EXCEPTION_MAXIMUM_PARAMETERS = 15

    class EXCEPTION_RECORD(ctypes.Structure):
        pass

    EXCEPTION_RECORD._fields_ = [
        ("ExceptionCode", wintypes.DWORD),
        ("ExceptionFlags", wintypes.DWORD),
        ("ExceptionRecord", ctypes.POINTER(EXCEPTION_RECORD)),
        ("ExceptionAddress", wintypes.LPVOID),
        ("NumberParameters", wintypes.DWORD),
        ("ExceptionInformation", ctypes.c_size_t * EXCEPTION_MAXIMUM_PARAMETERS),
    ]

    class EXCEPTION_POINTERS(ctypes.Structure):
        _fields_ = [
            ("ExceptionRecord", ctypes.POINTER(EXCEPTION_RECORD)),
            ("ContextRecord", wintypes.LPVOID),
        ]

    class MINIDUMP_EXCEPTION_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("ThreadId", wintypes.DWORD),
            ("ExceptionPointers", ctypes.POINTER(EXCEPTION_POINTERS)),
            ("ClientPointers", wintypes.BOOL),
        ]

    MiniDumpNormal = 0
    MiniDumpWithDataSegs = 0x00000004
    MiniDumpWithIndirectlyReferencedMemory = 0x00000040
    MiniDumpWithThreadInfo = 0x00001000
    MiniDumpWithFullMemory = 0x00000002

    _crash_dir = os.path.join(os.path.expanduser("~"), ".polaris_studio", "crash_dumps")
    _handler_ref: Any = None

    def _exception_code_name(code: int) -> str:
        names = {
            0xC0000005: "STATUS_ACCESS_VIOLATION",
            0xC0000094: "STATUS_INTEGER_DIVIDE_BY_ZERO",
            0xC00000FD: "STATUS_STACK_OVERFLOW",
            0xC0000409: "STATUS_STACK_BUFFER_OVERRUN",
            0xC0000374: "STATUS_HEAP_CORRUPTION",
            0x80000003: "STATUS_BREAKPOINT",
            0xC000001D: "STATUS_ILLEGAL_INSTRUCTION",
            0xC000008C: "STATUS_ARRAY_BOUNDS_EXCEEDED",
        }
        return names.get(code, f"0x{code & 0xFFFFFFFF:08X}")

    def _write_crash_report(rec: EXCEPTION_RECORD, dump_path: str | None) -> str:
        os.makedirs(_crash_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(_crash_dir, f"crash_{ts}_{os.getpid()}.log")

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("Polaris Studio crash report\n")
            f.write("=" * 60 + "\n")
            f.write(f"Timestamp:    {datetime.now().isoformat()}\n")
            f.write(f"PID:          {os.getpid()}\n")
            f.write(f"Python:       {sys.version.split()[0]}\n")
            f.write(f"Platform:     {sys.platform}\n\n")
            f.write(f"Exception:    {_exception_code_name(rec.ExceptionCode)}\n")
            f.write(f"Code:         0x{rec.ExceptionCode & 0xFFFFFFFF:08X}\n")
            f.write(f"Flags:        0x{rec.ExceptionFlags:08X}\n")
            f.write(f"Address:      0x{rec.ExceptionAddress:016X}\n")
            f.write(f"NumParams:    {rec.NumberParameters}\n")
            for i in range(min(rec.NumberParameters, 2)):
                f.write(f"  Param[{i}]:   0x{rec.ExceptionInformation[i]:016X}\n")
            f.write("\n")
            if dump_path and os.path.exists(dump_path):
                f.write(f"Minidump:     {dump_path}\n")
                f.write(f"  Size:       {os.path.getsize(dump_path)} bytes\n")
                f.write("  Analyze with: !analyze -v in WinDbg, or open in VS\n\n")
            f.write("Python stack (may be partial or missing for native crashes):\n")
            f.write("-" * 60 + "\n")
            try:
                f.write("".join(traceback.format_stack()[:50]))
            except Exception:
                f.write("(stack capture failed)\n")
        return log_path

    def _write_minidump(exception_info: ctypes.POINTER(EXCEPTION_POINTERS)) -> str | None:
        try:
            os.makedirs(_crash_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dump_path = os.path.join(_crash_dir, f"crash_{ts}_{os.getpid()}.dmp")

            dbghelp = ctypes.windll.dbghelp
            if not hasattr(dbghelp, "MiniDumpWriteDump"):
                return None

            MiniDumpWriteDump = dbghelp.MiniDumpWriteDump
            MiniDumpWriteDump.argtypes = [
                wintypes.HANDLE,
                wintypes.DWORD,
                wintypes.HANDLE,
                wintypes.DWORD,
                ctypes.POINTER(MINIDUMP_EXCEPTION_INFORMATION),
                wintypes.LPVOID,
                wintypes.LPVOID,
            ]
            MiniDumpWriteDump.restype = wintypes.BOOL

            kernel32 = ctypes.windll.kernel32
            CreateFileW = kernel32.CreateFileW
            CreateFileW.argtypes = [
                wintypes.LPCWSTR,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.LPVOID,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.HANDLE,
            ]
            CreateFileW.restype = wintypes.HANDLE

            INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
            GENERIC_WRITE = 0x40000000
            FILE_SHARE_WRITE = 2
            CREATE_ALWAYS = 2

            hFile = CreateFileW(
                dump_path,
                GENERIC_WRITE,
                FILE_SHARE_WRITE,
                None,
                CREATE_ALWAYS,
                0,
                None,
            )
            if not hFile or hFile == INVALID_HANDLE_VALUE:
                return None

            try:
                mdei = MINIDUMP_EXCEPTION_INFORMATION()
                mdei.ThreadId = kernel32.GetCurrentThreadId()
                mdei.ExceptionPointers = exception_info
                mdei.ClientPointers = False

                dump_type = (
                    MiniDumpWithDataSegs
                    | MiniDumpWithIndirectlyReferencedMemory
                    | MiniDumpWithThreadInfo
                )

                MiniDumpWriteDump(
                    kernel32.GetCurrentProcess(),
                    os.getpid(),
                    hFile,
                    dump_type,
                    ctypes.byref(mdei),
                    None,
                    None,
                )
            finally:
                kernel32.CloseHandle(hFile)

            return dump_path
        except Exception as e:
            try:
                err_path = os.path.join(_crash_dir, f"minidump_error_{os.getpid()}.log")
                with open(err_path, "w") as f:
                    f.write(f"minidump write failed: {e}\n{traceback.format_exc()}")
            except Exception:
                pass
            return None

    def _unhandled_exception_filter(exception_info: ctypes.POINTER(EXCEPTION_POINTERS)) -> int:
        try:
            rec = exception_info.contents.ExceptionRecord.contents
            dump_path = _write_minidump(exception_info)
            log_path = _write_crash_report(rec, dump_path)

            sys.stderr.write("\n" + "=" * 60 + "\n")
            sys.stderr.write(f"FATAL: {_exception_code_name(rec.ExceptionCode)}\n")
            sys.stderr.write(f"Log:    {log_path}\n")
            if dump_path:
                sys.stderr.write(f"Dump:   {dump_path}\n")
            sys.stderr.write("=" * 60 + "\n")
            sys.stderr.flush()
        except Exception:
            pass
        return EXCEPTION_EXECUTE_HANDLER

    EXCEPTION_HANDLER = ctypes.WINFUNCTYPE(wintypes.DWORD, ctypes.POINTER(EXCEPTION_POINTERS))

    def install_crash_handler() -> None:
        global _handler_ref
        try:
            kernel32 = ctypes.windll.kernel32
            _handler_ref = EXCEPTION_HANDLER(_unhandled_exception_filter)
            kernel32.SetUnhandledExceptionFilter(_handler_ref)
        except Exception:
            pass

    def get_crash_dir() -> str:
        return _crash_dir

else:

    def install_crash_handler() -> None:
        pass

    def get_crash_dir() -> str:
        return ""
