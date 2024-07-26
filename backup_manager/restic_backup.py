import os
from datetime import datetime

from i18n import _  # Import the _ variable
from utils import format_duration, log_and_email


class ResticBackup:
    def __init__(self, config, logger, command_runner, backup_manager):
        self.config = config
        self.logger = logger
        self.command_runner = command_runner
        self.backup_manager = backup_manager
        self.backup_paths = self.detect_services()

    def detect_services(self):
        backup_paths = set(self.config.DEFAULT_PATHS)
        for service, paths in self.config.SERVICE_CONFIGS.items():
            if any(os.path.isdir(path) for path in paths):
                backup_paths.update(paths)
        return list(backup_paths)

    def is_restic_locked(self, repository, password_file):
        check_lock_command = f"restic -r {repository} --password-file {password_file} unlock"
        return_code, stdout, stderr = self.command_runner.run(check_lock_command, verbose=True)
        if return_code != 0 and _("repository is already locked") in stderr:
            return True
        return False

    def apply_retention_policy(self, repository, password_file):
        log_and_email(self.backup_manager, self.logger, _("Retention Policy"), section=True)
        log_and_email(self.backup_manager, self.logger, _("Applying retention policy..."))
        if self.is_restic_locked(repository, password_file):
            error_message = _(
                "Error: Restic repository is locked! Cannot apply retention policy. Use `restic unlock` to unlock the repository.")
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
            log_and_email(self.backup_manager, self.logger,
                          _("Retention policy applied successfully in {}.").format(retention_duration))

    @staticmethod
    def should_run_backup():
        today = datetime.now().day
        if today == 1:
            return 'monthly'
        elif today % 7 == 0:
            return 'weekly'
        else:
            return 'daily'

    def run_backup(self):
        backup_type = self.should_run_backup()
        if backup_type:
            log_and_email(self.backup_manager, self.logger, f"Restic {backup_type.capitalize()} " + _("Backup"),
                          section=True)
            log_and_email(self.backup_manager, self.logger, _("Starting Restic {} backup...").format(backup_type))
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
                log_and_email(self.backup_manager, self.logger,
                              _("Restic {} backup completed successfully in {}.").format(backup_type, restic_duration))
                files_processed = stdout.count("processed")
                backup_size_line = next((line for line in stdout.splitlines() if "Added to the repository:" in line),
                                        None)
                if backup_size_line:
                    data_transferred, data_stored = self.extract_backup_size(backup_size_line)
                    log_and_email(self.backup_manager, self.logger,
                                  _("Files processed: {}, Data transferred: {}, Data stored: {}").format(
                                      files_processed, data_transferred, data_stored))
                else:
                    log_and_email(self.backup_manager, self.logger,
                                  _("Files processed: {}, Backup size: unknown").format(files_processed))

            log_and_email(self.backup_manager, self.logger, _("Backup Size Information"), section=True)
            uncompressed_size = self.get_uncompressed_size()
            compressed_size = self.get_compressed_size()
            total_backup_size = self.calculate_total_backup_size()

            log_and_email(self.backup_manager, self.logger,
                          _("Restic repository uncompressed size: {}").format(uncompressed_size))
            log_and_email(self.backup_manager, self.logger,
                          _("Restic repository compressed size: {}").format(compressed_size))
            log_and_email(self.backup_manager, self.logger,
                          _("Total size of backup folder: {:.2f} MB").format(total_backup_size))

            self.apply_retention_policy(self.config.RESTIC_REPOSITORY, self.config.RESTIC_PASSWORD_FILE)

    def extract_backup_size(self, backup_size_line):
        data_transferred = backup_size_line.split("Added to the repository:")[1].split(" (")[0].strip()
        data_stored = backup_size_line.split("(")[1].split(" stored")[0].strip()
        return data_transferred, data_stored

    def get_uncompressed_size(self):
        stats_command = f"restic -r {self.config.RESTIC_REPOSITORY} --password-file {self.config.RESTIC_PASSWORD_FILE} stats --mode restore-size"
        return_code, stdout, stderr = self.command_runner.run(stats_command, verbose=True, timeout=300)
        if return_code == 0:
            uncompressed_size_line = next((line for line in stdout.splitlines() if "Total Size" in line), None)
            if uncompressed_size_line:
                return uncompressed_size_line.split(":")[1].strip()
        return _("unknown")

    def get_compressed_size(self):
        du_command = f"du -sh {self.config.RESTIC_REPOSITORY}"
        return_code, stdout, stderr = self.command_runner.run(du_command, verbose=True, timeout=300)
        if return_code == 0:
            return stdout.split()[0]
        return _("unknown")

    def calculate_total_backup_size(self):
        backup_dir_size = self.get_dir_size(self.config.BASE_BACKUP_DIR)
        size_in_mb = backup_dir_size / (1024 * 1024)
        return size_in_mb

    @staticmethod
    def get_dir_size(directory):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size
