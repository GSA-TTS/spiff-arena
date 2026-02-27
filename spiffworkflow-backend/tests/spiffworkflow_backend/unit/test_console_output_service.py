from flask.app import Flask

from spiffworkflow_backend.services.console_output_service import ConsoleOutputBuffer
from spiffworkflow_backend.services.console_output_service import console_capture
from spiffworkflow_backend.services.console_output_service import get_active_console_buffer
from spiffworkflow_backend.services.process_instance_processor import _console_print


class TestConsoleOutputService:
    def test_console_output_buffer_write_and_drain(self, app: Flask) -> None:
        buf = ConsoleOutputBuffer()
        buf.write("line one\n")
        buf.write("line two\n")
        result = buf.drain()
        assert result == ["line one\n", "line two\n"]

        # drain again should be empty
        assert buf.drain() == []

    def test_console_capture_sets_and_clears_thread_local(self, app: Flask) -> None:
        assert get_active_console_buffer() is None

        with console_capture() as buf:
            assert get_active_console_buffer() is buf

        assert get_active_console_buffer() is None

    def test_console_print_writes_to_active_buffer(self, app: Flask) -> None:
        with console_capture() as buf:
            _console_print("hello", "world")
            lines = buf.drain()
        assert lines == ["hello world\n"]

    def test_console_print_without_active_buffer_does_not_raise(self, app: Flask) -> None:
        # When no buffer is active, _console_print should just log and not raise
        _console_print("this goes to the log")
