"""Thread-safe buffer for capturing print() output during script task execution."""

import contextlib
import threading
from collections import deque
from collections.abc import Generator
from typing import Any


class ConsoleOutputBuffer:
    """Thread-safe buffer that captures text output."""

    def __init__(self) -> None:
        self._buffer: deque[str] = deque()
        self._lock = threading.Lock()

    def write(self, text: str) -> None:
        with self._lock:
            self._buffer.append(text)

    def drain(self) -> list[str]:
        """Return all buffered lines and clear the buffer."""
        with self._lock:
            lines = list(self._buffer)
            self._buffer.clear()
        return lines

    def flush(self) -> None:
        pass


# Thread-local storage for the active console buffer
_thread_local = threading.local()


def get_active_console_buffer() -> ConsoleOutputBuffer | None:
    return getattr(_thread_local, "console_buffer", None)


@contextlib.contextmanager
def console_capture() -> Generator[ConsoleOutputBuffer, Any, None]:
    """Context manager that sets the active console buffer for the current thread.

    Script tasks use _console_print() which checks for the active buffer.

    Usage:
        with console_capture() as buf:
            # any _console_print() calls will write to buf
            do_engine_steps()
            lines = buf.drain()
    """
    buf = ConsoleOutputBuffer()
    _thread_local.console_buffer = buf
    try:
        yield buf
    finally:
        _thread_local.console_buffer = None
