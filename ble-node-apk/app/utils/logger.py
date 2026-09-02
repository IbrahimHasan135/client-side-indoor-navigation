from __future__ import annotations

from datetime import datetime


class AppLogger:
    """Small logger wrapper so non-UI layers do not depend on Kivy widgets."""

    def info(self, tag: str, message: str) -> None:
        self._write("INFO", tag, message)

    def warning(self, tag: str, message: str) -> None:
        self._write("WARN", tag, message)

    def error(self, tag: str, message: str) -> None:
        self._write("ERROR", tag, message)

    def _write(self, level: str, tag: str, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{timestamp} [{level}] {tag}: {message}")
