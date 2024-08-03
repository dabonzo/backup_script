# backup_manager/backup_manager.py
import os
from datetime import datetime
from .database_backup import DatabaseBackup
from .email_notifier import EmailNotifier
from .log_cleaner import LogCleaner
from .restic_backup import ResticBackup
from .software_list_generator import SoftwareListGenerator
from utils import format_duration

class BackupManager:
    """
    Manage the overall backup process.
    """
    def __init__(self, config, logger, command_runner):
        """
        Initialize the BackupManager class.
        :param config: Configuration object.
        :param logger: Logger object.
        :param command_runner: CommandRunner object.
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
        Perform the entire backup process.
        """
        start_time = datetime.now()
        self.logger.log(_("Backup Process Started"), section=True)
        current_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
        timestamp = start_time.strftime("%Y%m%d%H%M%S")
        self.email_body = f"<html><body><h2>{_('Backup Summary for')} {self.config.SERVER_NAME} - {current_time}</h2>"
        self.logger.log(f"{_('Backup started at')} {current_time}")

        # Perform database backup
        self.database_backup.backup()

        # Perform Restic backup
        self.restic_backup.run_backup()

        # Perform software list generation
        self.software_list_generator.generate()

        # Clean up old logs
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

        # Write the backup status to the centralized location
        status_file_path = os.path.join(self.config.STATUS_FILE_DIR, f"backup_status_{self.config.SERVER_NAME}_{timestamp}.txt")
        with open(status_file_path, "w") as status_file:
            status_file.write(f"Server: {self.config.SERVER_NAME}\n")
            status_file.write(f"Status: {'Success' if self.backup_success else 'Failed'}\n")
            status_file.write(f"Start Time: {current_time}\n")
            status_file.write(f"End Time: {end_time_str}\n")
            status_file.write(f"Duration: {total_duration}\n")
            if not self.backup_success:
                status_file.write(f"Log File: {self.config.LOG_FILE}\n")

        try:
            if not self.backup_success:
                email_notifier.send_email(email_subject, self.config.EMAIL_TO, self.config.EMAIL_FROM, self.config.EMAIL_BODY_PATH, self.config.LOG_FILE)
            else:
                if self.config.SEND_SUCCESS_EMAIL:
                    email_notifier.send_email(email_subject, self.config.EMAIL_TO, self.config.EMAIL_FROM, self.config.EMAIL_BODY_PATH)
        except RuntimeError as e:
            self.logger.log(f"Error sending email: {str(e)}")
            with open(status_file_path, "a") as status_file:
                status_file.write(f"Email Status: Failed to send\n")
                status_file.write(f"Email Error: {str(e)}\n")

        os.remove(self.config.EMAIL_BODY_PATH)
