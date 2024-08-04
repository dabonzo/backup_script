# backup_manager/restic_backup.py
import os
import random
from datetime import datetime
from .base_backup import BaseBackup
from i18n import _
from utils import format_duration, log_and_email, is_restic_locked, BackupSizeCalculator


class ResticBackup(BaseBackup):
    """
    Class to handle Restic backup operations.
    """

    def __init__(self, config, logger, command_runner, backup_manager):
        """
        Initialize the ResticBackup class.
        :param config: Configuration object.
        :param logger: Logger object.
        :param command_runner: CommandRunner object.
        :param backup_manager: BackupManager object.
        """
        super().__init__(config, logger, backup_manager)
        self.command_runner = command_runner
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

    def apply_retention_policy(self):
        """
        Apply the retention policy to the Restic repository.
        """
        log_and_email(self.backup_manager, self.logger, _("Applying retention policy..."))

        if is_restic_locked(self.config.RESTIC_REPOSITORY, self.config.RESTIC_PASSWORD_FILE, self.command_runner,
                            self.logger):
            self._handle_locked_repository("Error: Restic repository is locked! Cannot apply retention policy.")
            return

        forget_command = f"restic -r {self.config.RESTIC_REPOSITORY} --password-file {self.config.RESTIC_PASSWORD_FILE} forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --keep-yearly 1 --prune"
        self._run_retention_command(forget_command)

    def _handle_locked_repository(self, message):
        """
        Handle the case where the Restic repository is locked.
        :param message: Error message.
        """
        error_message = _(message + " Use `restic unlock` to unlock the repository.")
        log_and_email(self.backup_manager, self.logger, error_message, error=True)
        self.backup_manager.backup_success = False

    def _run_retention_command(self, forget_command):
        """
        Run the Restic forget command to apply the retention policy.
        :param forget_command: Command to apply the retention policy.
        """
        retention_start_time = datetime.now()
        return_code, stdout, stderr = self.command_runner.run(forget_command, verbose=True, timeout=3600)
        retention_end_time = datetime.now()
        retention_duration = format_duration(retention_end_time - retention_start_time)

        if return_code != 0:
            error_message = _("Error: Retention policy application failed! See log for details at line {}.").format(
                len(open(self.config.LOG_FILE).readlines()) + 1)
            log_and_email(self.backup_manager, self.logger, error_message, error=True)
            self.backup_manager.backup_success = False
        else:
            log_and_email(self.backup_manager, self.logger,
                          _("Retention policy applied successfully in {}.").format(retention_duration))

    @staticmethod
    def should_run_backup():
        """
        Determine the type of backup to run based on the current date.
        :return: Type of backup to run ('monthly', 'weekly', or 'daily').
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
            self._start_backup_process(backup_type)

    def _start_backup_process(self, backup_type):
        """
        Start the Restic backup process for the specified backup type.
        :param backup_type: Type of backup to run.
        """
        log_and_email(self.backup_manager, self.logger, f"Restic {backup_type.capitalize()} " + _("Backup"),
                      section=True)
        log_and_email(self.backup_manager, self.logger, _("Starting Restic {} backup...").format(backup_type))

        if is_restic_locked(self.config.RESTIC_REPOSITORY, self.config.RESTIC_PASSWORD_FILE, self.command_runner,
                            self.logger):
            self._handle_locked_repository("Error: Restic repository is locked! Cannot start backup.")
            return

        # Simulate failure
        simulate_failure = self.config.SIMULATE_FAILURES and False

        if simulate_failure:
            self._simulate_failure()
            return

        restic_start_time = datetime.now()
        backup_command = f"restic -r {self.config.RESTIC_REPOSITORY} --password-file {self.config.RESTIC_PASSWORD_FILE} backup {' '.join(self.backup_paths)}"
        return_code, stdout, stderr = self.command_runner.run(backup_command, verbose=True, timeout=3600)
        restic_end_time = datetime.now()
        restic_duration = format_duration(restic_end_time - restic_start_time)

        if return_code != 0:
            error_message = _("Error: Restic {} backup failed! See log for details at line {}.").format(backup_type,
                                                                                                        len(open(
                                                                                                            self.config.LOG_FILE).readlines()) + 1)
            log_and_email(self.backup_manager, self.logger, error_message, error=True)
            self.backup_manager.backup_success = False
        else:
            self._log_backup_success(stdout, backup_type, restic_duration)

        self._log_backup_size_info()

        self.apply_retention_policy()

    def _simulate_failure(self):
        """
        Simulate a failure in the Restic backup process.
        """
        non_existent_path = "/non_existent_path"
        self.logger.log(_("Simulating failure for backup path: {}").format(non_existent_path))
        restic_start_time = datetime.now()
        backup_command = f"restic -r {self.config.RESTIC_REPOSITORY} --password-file {self.config.RESTIC_PASSWORD_FILE} backup {non_existent_path}"
        return_code, stdout, stderr = self.command_runner.run(backup_command, verbose=True, timeout=3600)
        restic_end_time = datetime.now()
        self._handle_error("Error: Restic backup failed for simulated path!", stderr)

    def _log_backup_success(self, stdout, backup_type, restic_duration):
        """
        Log the success of the Restic backup process.
        :param stdout: Standard output from the backup command.
        :param backup_type: Type of backup that was run.
        :param restic_duration: Duration of the backup process.
        """
        log_and_email(self.backup_manager, self.logger,
                      _("Restic {} backup completed successfully in {}.").format(backup_type, restic_duration))
        files_processed = stdout.count("processed")
        backup_size_line = next((line for line in stdout.splitlines() if "Added to the repository:" in line), None)
        if backup_size_line:
            data_transferred, data_stored = self.size_calculator.extract_backup_size(backup_size_line)
            log_and_email(self.backup_manager, self.logger,
                          _("Files processed: {}, Data transferred: {}, Data stored: {}").format(files_processed,
                                                                                                 data_transferred,
                                                                                                 data_stored))
        else:
            log_and_email(self.backup_manager, self.logger,
                          _("Files processed: {}, Backup size: unknown").format(files_processed))

    def _log_backup_size_info(self):
        """
        Log information about the backup size.
        """
        log_and_email(self.backup_manager, self.logger, _("Backup Size Information"), section=True)
        uncompressed_size = self.size_calculator.get_uncompressed_size()
        compressed_size = self.size_calculator.get_compressed_size()
        total_backup_size = self.size_calculator.calculate_total_backup_size()

        log_and_email(self.backup_manager, self.logger,
                      _("Restic repository uncompressed size: {}").format(uncompressed_size))
        log_and_email(self.backup_manager, self.logger,
                      _("Restic repository compressed size: {}").format(compressed_size))
        log_and_email(self.backup_manager, self.logger,
                      _("Total size of backup folder: {:.2f} MB").format(total_backup_size))
