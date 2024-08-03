# backup_manager/base_backup.py
from i18n import _

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
        error_message = _(message + " See log for details at line {}.").format(len(open(self.config.LOG_FILE).readlines()) + 1)
        self.backup_manager.email_body += f"<strong style='color: red;'>{error_message}</strong><br>\n"
        self.logger.log(f"{message} {stderr}")
        self.backup_manager.error_lines.append(error_message)
        self.backup_manager.backup_success = False
