# backup_manager/backup_manager.py
import os
from datetime import datetime

from backup_manager.database_backup import DatabaseBackup
from backup_manager.email_notifier import EmailNotifier
from backup_manager.log_cleaner import LogCleaner
from backup_manager.restic_backup import ResticBackup
from backup_manager.software_list_generator import SoftwareListGenerator
from utils import format_duration
from i18n import get_translation
_ = get_translation()

class BackupManager:
    """
    Class to manage the backup operations.
    """
    def __init__(self, config, logger, command_runner):
        """
        Initialize the BackupManager class.
        :param config: Configuration object containing backup settings.
        :param logger: Logger object for logging messages.
        :param command_runner: CommandRunner object to execute shell commands.
        """
        self.config = config
        self.logger = logger
        self.command_runner = command_runner
        self.email_body = ""
        self.error_lines = []
        self.backup_success = True

        self.database_backup = DatabaseBackup(config, logger, command_runner, self)
        self.restic_backup = ResticBackup(config, logger, command_runner, self)
        self.software_list_generator = SoftwareListGenerator(config, logger, command_runner, self)

        self.log_cleaner = LogCleaner(config, logger)

    def backup(self):
        """
        Perform the backup operations.
        """
        start_time = datetime.now()
        self.logger.log(_("Backup Process Started"), section=True)

        current_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
        self.email_body = f"<html><body><h2>{_('Backup Summary for')} {self.config.SERVER_NAME} - {current_time}</h2>"
        self.logger.log(f"{_('Backup started at')} {current_time}")

        self.database_backup.backup()
        self.restic_backup.run_backup()
        self.software_list_generator.generate()

        self.log_cleaner.clean(self.config.LOG_DIR, self.config.RETENTION_DAYS)

        end_time = datetime.now()
        total_duration = format_duration(end_time - start_time)
        end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')

        self.logger.log(_("Backup Process Completed"), section=True)
        self.logger.log(f"{_('Backup completed at')} {end_time_str}")
        self.logger.log(f"{_('Total backup duration')} {total_duration}")

        self.email_body += f"<h2>{_('Backup Time Details')}</h2>"
        self.email_body += f"<p>{_('Backup started at')}: {current_time}</p>"
        self.email_body += f"<p>{_('Backup completed at')}: {end_time_str}</p>"
        self.email_body += f"<p>{_('Total backup duration')}: {total_duration}</p>"
        self.email_body += "</body></html>"

        with open(self.config.EMAIL_BODY_PATH, "w") as email_file:
            email_file.write(self.email_body)

        email_subject = f"{_('Backup')} {'Success' if self.backup_success else _('Failed')} {_('for')} {self.config.SERVER_NAME} - {datetime.now().strftime('%Y-%m-%d')}"

        email_notifier = EmailNotifier(self.config.SMTP_SERVER, self.config.SMTP_PORT, self.config.SMTP_USERNAME, self.config.SMTP_PASSWORD)

        if not self.backup_success:
            email_notifier.send_email(email_subject, self.config.EMAIL_TO, self.config.EMAIL_FROM, self.config.EMAIL_BODY_PATH, self.config.LOG_FILE)
        else:
            email_notifier.send_email(email_subject, self.config.EMAIL_TO, self.config.EMAIL_FROM, self.config.EMAIL_BODY_PATH)

        os.remove(self.config.EMAIL_BODY_PATH)
