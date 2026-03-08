import os
import logging
import time
from datetime import datetime
import re

class _CleanAnsiFormatter(logging.Formatter):
    def __init__(self, fmt, ansi_re):
        super().__init__(fmt)
        self._ansi_re = ansi_re

    def format(self, record):
        # Strip ANSI from record.msg (string messages)
        if isinstance(record.msg, str):
            record.msg = self._ansi_re.sub("", record.msg)

        # Strip ANSI from record.args (Werkzeug often puts the colored text here)
        args = record.args

        if isinstance(args, tuple):
            cleaned = []
            for a in args:
                if isinstance(a, str):
                    cleaned.append(self._ansi_re.sub("", a))
                else:
                    cleaned.append(a)
            record.args = tuple(cleaned)

        elif isinstance(args, dict):
            cleaned = {}
            for k, v in args.items():
                if isinstance(v, str):
                    cleaned[k] = self._ansi_re.sub("", v)
                else:
                    cleaned[k] = v
            record.args = cleaned

        return super().format(record)

class MyLogger:
    """
    A class to set up and manage logging.
    """

    def __init__(self, log_folder="logs"):
        """
        Initialize the logger with a specified log folder.
        """
        self.log_folder = log_folder
        self._last_time_check = None
        self._ansi_re = re.compile(r"\x1b\[[0-9;]*m")
        self._setup_logging()

    def _setup_logging(self):
        """
        Configure logging settings.
        """
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)

        log_filename = os.path.join(self.log_folder, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

        # Replace the formatter on the file handler(s) with an ANSI-stripping one
        clean_fmt = _CleanAnsiFormatter("%(asctime)s - %(levelname)s - %(message)s", self._ansi_re)
        root = logging.getLogger()
        for h in root.handlers:
            if isinstance(h, logging.FileHandler):
                h.setFormatter(clean_fmt)

        self.info("++++++++++++++")
        self.info("Logging setup complete.")
        self._cleanup_old_logs()  # Add this line

    def log_time(self, label):
        now = time.time()
        if self._last_time_check is None:
            self._last_time_check = now
        elapsed = now - self._last_time_check
        self._last_time_check = now
        self.info(f"{label} - {time.strftime('%H:%M:%S')} - +{elapsed:.3f}s")

    def _cleanup_old_logs(self, days=7):
        """
        Delete log files older than the specified number of days.
        """
        now = time.time()
        cutoff = now - (days * 86400)

        for filename in os.listdir(self.log_folder):
            file_path = os.path.join(self.log_folder, filename)
            if os.path.isfile(file_path) and filename.endswith(".log"):
                if os.path.getmtime(file_path) < cutoff:
                    try:
                        os.remove(file_path)
                        self.info(f"Deleted old log file: {file_path}")
                    except Exception as e:
                        self.warning(f"Failed to delete {file_path}: {e}")
        self.info("Log cleanup complete.")                        


    # Adding the standard logging methods
    def info(self, message):
        logging.info(message)

    def warning(self, message):
        logging.warning(message)

    def error(self, message):
        logging.error(message)

    def debug(self, message):
        logging.debug(message)

    def critical(self, message):
        logging.critical(message)
