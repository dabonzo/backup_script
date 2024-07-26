import os
from datetime import datetime, timedelta

from i18n import _


class LogCleaner:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def clean(self, directory, days):
        cutoff_date = datetime.now() - timedelta(days=days)
        logs = sorted(os.listdir(directory), key=lambda x: os.path.getmtime(os.path.join(directory, x)))
        for log in logs[:-days]:
            log_path = os.path.join(directory, log)
            os.remove(log_path)
            self.logger.log(_("Removed old log file: {}").format(log_path))
