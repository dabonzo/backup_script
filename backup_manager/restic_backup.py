# backup_manager/restic_backup.py
import os
from datetime import datetime

from i18n import _
from utils import format_duration, log_and_email, is_restic_locked, BackupSizeCalculator

class ResticBackup:
    """
    Class to handle Restic backup operations.
    """
    def __init__(self, config, logger, command_runner, backup_manager):
        """
        Initialize the ResticBackup class.
        :param config: Configuration object containing backup settings.
        :param logger: Logger object for logging messages.
        :param command_runner: CommandRunner object to execute shell commands.
        :param backup_manager: BackupManager object to manage backup operations.
        """
        self.config = config
        self.logger = logger
        self.command_runner = command_runner
        self.backup_manager = backup_manager
        self.backup_paths = self.detect_services()
        self.size_calculator = BackupSizeCalculator(config, command_runner, logger)

    def detect_services(self):
        """
        Detect and return the list of backup paths for configured services.
        :return: List of backup paths.
        """
        backup_paths = set(self.config.DEFAULT_PATHS)
        for service, paths in self.config.SERVICE_CONFIGS.items():
            if any(os.path.isdir(path) for path in paths):
                backup_paths.update(paths)
        return list(backup_paths)

    def apply_retention_policy(self, repository, password_file):
        """
        Apply the retention policy to the Restic repository.
        :param repository: Path to the Restic repository.
        :param password_file: Path to the password file.
        """
        log_and_email(self.backup_manager, self.logger, _("Applying retention policy..."))

        if is_restic_locked(repository, password_file, self.command_runner, self.logger):
            error_message = _("Error: Restic repository is locked! Cannot apply retention policy. Use `restic unlock` to unlock the repository.")
            log_and_email(self.backup_manager, self.logger, error_message, error=True)
            self.backup_manager.backup_success = False
            return
        forget_command = f"restic -r {repository} --password-file {password_file} forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --keep-yearly 1 --prune"
        retention_start_time = datetime.now()
        return_code, stdout, stderr = self.command_runner.run(forget_command, verbose=True, timeout=600)
        retention_end_time = datetime.now()
        retention_duration = format_duration(retention_end_time - retention_start_time)

        if return_code != 0:
            error_message = _("Error: Retention policy application failed! See log for details at line {}.").format(
                len(open(self.config.LOG_FILE).readlines()) + 1)
            log_and_email(self.backup_manager, self.logger, error_message, error=True)
            self.backup_manager.backup_success = False
        else:
            log_and_email(self.backup_manager, self.logger, _("Retention policy applied successfully in {}.").format(retention_duration))

    @staticmethod
    def should_run_backup():
        """
        Determine the type of backup to run based on the current date.
        :return: The type of backup to run ('daily', 'weekly', or 'monthly').
        """
        today = datetime.now().day
        if today == 1:
            return 'monthly'
        elif today % 7 == 0:
            return 'weekly'
        else:
            return 'daily'

    def run_backup(self):
        """
        Run the Restic backup process.
        """
        backup_type = self.should_run_backup()
        if backup_type:
            log_and_email(self.backup_manager, self.logger, f"Restic {backup_type.capitalize()} " + _("Backup"), section=True)
            log_and_email(self.backup_manager, self.logger, _("Starting Restic {} backup...").format(backup_type))

            # Check if the repository is locked before starting the backup
            if is_restic_locked(self.config.RESTIC_REPOSITORY, self.config.RESTIC_PASSWORD_FILE, self.command_runner, self.logger):
                error_message = _("Error: Restic repository is locked! Cannot start backup. Use `restic unlock` to unlock the repository.")
                log_and_email(self.backup_manager, self.logger, error_message, error=True)
                self.backup_manager.backup_success = False
                return
            restic_start_time = datetime.now()
            backup_command = f"restic -r {self.config.RESTIC_REPOSITORY} --password-file {self.config.RESTIC_PASSWORD_FILE} backup {' '.join(self.backup_paths)}"
            return_code, stdout, stderr = self.command_runner.run(backup_command, verbose=True, timeout=3600)
            restic_end_time = datetime.now()
            restic_duration = format_duration(restic_end_time - restic_start_time)
            if return_code != 0:
                error_message = _("Error: Restic {} backup failed! See log for details at line {}.").format(backup_type, len(open(self.config.LOG_FILE).readlines()) + 1)
                log_and_email(self.backup_manager, self.logger, error_message, error=True)
                self.backup_manager.backup_success = False
            else:
                log_and_email(self.backup_manager, self.logger, _("Restic {} backup completed successfully in {}.").format(backup_type, restic_duration))
                files_processed = stdout.count("processed")
                backup_size_line = next((line for line in stdout.splitlines() if "Added to the repository:" in line), None)
                if backup_size_line:
                    data_transferred, data_stored = self.size_calculator.extract_backup_size(backup_size_line)
                    log_and_email(self.backup_manager, self.logger, _("Files processed: {}, Data transferred: {}, Data stored: {}").format(files_processed, data_transferred, data_stored))
                else:
                    log_and_email(self.backup_manager, self.logger, _("Files processed: {}, Backup size: unknown").format(files_processed))

            log_and_email(self.backup_manager, self.logger, _("Backup Size Information"), section=True)
            uncompressed_size = self.size_calculator.get_uncompressed_size()
            compressed_size = self.size_calculator.get_compressed_size()
            total_backup_size = self.size_calculator.calculate_total_backup_size()

            log_and_email(self.backup_manager, self.logger, _("Restic repository uncompressed size: {}").format(uncompressed_size))
            log_and_email(self.backup_manager, self.logger, _("Restic repository compressed size: {}").format(compressed_size))
            log_and_email(self.backup_manager, self.logger, _("Total size of backup folder: {:.2f} MB").format(total_backup_size))

            self.apply_retention_policy(self.config.RESTIC_REPOSITORY, self.config.RESTIC_PASSWORD_FILE)
