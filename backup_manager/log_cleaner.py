# backup_manager/log_cleaner.py
import os
from datetime import datetime, timedelta
from i18n import _

class LogCleaner:
    """
    Class to handle cleaning old log files.
    """
    def __init__(self, config, logger):
        """
        Initialize the LogCleaner class.
        :param config: Configuration object.
        :param logger: Logger object.
        """
        self.config = config
        self.logger = logger

    def clean(self, directory, days):
        """
        Clean log files older than the specified number of days.
        :param directory: Directory containing log files.
        :param days: Number of days to retain log files.
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        logs = sorted(os.listdir(directory), key=lambda x: os.path.getmtime(os.path.join(directory, x)))
        for log in logs[:-days]:
            log_path = os.path.join(directory, log)
            os.remove(log_path)
            self.logger.log(_("Removed old log file: {}").format(log_path))
