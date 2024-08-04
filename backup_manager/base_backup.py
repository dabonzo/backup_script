# backup_manager/base_backup.py
from i18n import _
from utils import handle_error

class BaseBackup:
    """
    Base class for common backup operations.
    """
    def __init__(self, config, logger, backup_manager):
        """
        Initialize the BaseBackup class.
        :param config: Configuration object.
        :param logger: Logger object.
        :param backup_manager: BackupManager object.
        """
        self.config = config
        self.logger = logger
        self.backup_manager = backup_manager

    def _handle_error(self, message, stderr):
        """
        Handle an error during the backup process.
        :param message: Error message.
        :param stderr: Error output.
        """
        handle_error(message, stderr, self.config, self.logger, self.backup_manager)
