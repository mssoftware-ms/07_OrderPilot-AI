from __future__ import annotations

import ctypes
import sys

def _is_windows() -> bool:
    return sys.platform.startswith("win")

def _get_console_hwnd() -> int:
    if not _is_windows():
        return 0
    return ctypes.windll.kernel32.GetConsoleWindow()

def _hide_console_window() -> None:
    if not _is_windows():
        return
    hwnd = _get_console_hwnd()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)

def _show_console_window() -> None:
    if not _is_windows():
        return
    hwnd = _get_console_hwnd()
    if not hwnd:
        ctypes.windll.kernel32.AllocConsole()
        hwnd = _get_console_hwnd()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 5)
