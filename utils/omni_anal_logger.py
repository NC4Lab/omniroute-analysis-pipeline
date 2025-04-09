"""
Module: omni_anal_logger.py

Purpose:
    Lightweight utility for structured logging with elapsed time tracking and nested operations.
"""

import time
from datetime import datetime

class OmniAnalLogger:
    def __init__(self):
        self.indent_level = 0
        self.indent_str = "    "

    def _timestamp(self) -> str:
        now = datetime.now()
        ms = int(now.microsecond / 1000)
        return f"[{now.hour:02}:{now.minute:02}:{now.second:02}.{ms:03}]"

    def _indent(self) -> str:
        return self.indent_str * self.indent_level

    def info(self, message: str) -> None:
        """
        Log a simple info message with indentation and timestamp.

        Parameters:
            message (str): The message to print.
        """
        print(f"{self._timestamp()} {self._indent()}{message}")

    def start(self, message: str) -> float:
        """
        Log the start of a long-running operation.

        Parameters:
            message (str): Description of the operation.

        Returns:
            float: Start time (use with .end())
        """
        self.info(f"Starting: {message}")
        self.indent_level += 1
        return time.time()

    def end(self, start_time: float) -> None:
        """
        Log the end of an operation started with .start()

        Parameters:
            start_time (float): The start time returned by .start()
        """
        elapsed = time.time() - start_time
        seconds = int(elapsed)
        milliseconds = int((elapsed - seconds) * 1000)
        self.indent_level = max(0, self.indent_level - 1)
        self.info(f"Finished in {seconds:02}.{milliseconds:03}s")

    def time_block(self, message: str):
        """
        Context manager for timing a code block.

        Parameters:
            message (str): Description of the block being timed.

        Usage:
            with omni_anal_logger.time_block("Step name"):
                do_work()
        """
        return _TimerContext(self, message)


class _TimerContext:
    def __init__(self, omni_anal_logger: OmniAnalLogger, message: str):
        self.omni_anal_logger = omni_anal_logger
        self.message = message
        self.start_time = None

    def __enter__(self):
        self.start_time = self.omni_anal_logger.start(self.message)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.end(self.start_time)


# Instantiate a default global logger for convenience
omni_anal_logger = OmniAnalLogger()
