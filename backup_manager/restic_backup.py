import gettext
import os
from datetime import datetime

_ = gettext.gettext


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
        self.logger.log(_("Applying Retention Policy"), section=True)
        self.backup_manager.email_body += "<h2>" + _("Applying Retention Policy") + "</h2>\n"
        self.logger.log(_("Applying retention policy..."))
        if self.is_restic_locked(repository, password_file):
            error_message = _(
                "Error: Restic repository is locked! Cannot apply retention policy. Use `restic unlock` to unlock the repository.")
            self.backup_manager.email_body += f"<strong style='color: red;'>{error_message}</strong>\n"
            self.logger.log(error_message)
            self.backup_manager.error_lines.append(error_message)
            self.backup_manager.backup_success = False
            return
        forget_command = f"restic -r {repository} --password-file {password_file} forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --keep-yearly 1 --prune"
        retention_start_time = datetime.now()
        return_code, stdout, stderr = self.command_runner.run(forget_command, verbose=True, timeout=600)
        retention_end_time = datetime.now()
        retention_duration = retention_end_time - retention_start_time
        if return_code != 0:
            error_message = _("Error: Retention policy application failed! See log for details at line {}.").format(
                len(open(self.config.LOG_FILE).readlines()) + 1)
            self.backup_manager.email_body += f"<strong style='color: red;'>{error_message}</strong>\n"
            self.logger.log(_("Error: Retention policy application failed!"))
            self.backup_manager.error_lines.append(error_message)
            self.backup_manager.backup_success = False
        else:
            self.backup_manager.email_body += _("Retention policy applied successfully.") + "\n"
            self.logger.log(_("Retention policy applied successfully in {}.").format(retention_duration))

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
            self.logger.log(f"Restic {backup_type.capitalize()} " + _("Backup"), section=True)
            self.backup_manager.email_body += f"<h2>Restic {backup_type.capitalize()} " + _("Backup") + "</h2>\n"
            self.logger.log(_("Starting Restic {} backup...").format(backup_type))
            restic_start_time = datetime.now()
            backup_command = f"restic -r {self.config.RESTIC_REPOSITORY} --password-file {self.config.RESTIC_PASSWORD_FILE} backup {' '.join(self.backup_paths)}"
            return_code, stdout, stderr = self.command_runner.run(backup_command, verbose=True, timeout=3600)
            restic_end_time = datetime.now()
            restic_duration = restic_end_time - restic_start_time
            if return_code != 0:
                error_message = _("Error: Restic {} backup failed! See log for details at line {}.").format(backup_type,
                                                                                                            len(open(
                                                                                                                self.config.LOG_FILE).readlines()) + 1)
                self.backup_manager.email_body += f"<strong style='color: red;'>{error_message}</strong>\n"
                self.logger.log(f"Error: Restic {backup_type} backup failed! {stderr}")
                self.backup_manager.error_lines.append(error_message)
                self.backup_manager.backup_success = False
            else:
                self.backup_manager.email_body += _("Restic {} backup completed successfully.").format(
                    backup_type) + "\n"
                self.logger.log(
                    _("Restic {} backup completed successfully in {}.").format(backup_type, restic_duration))
                files_processed = stdout.count(_("processed"))
                backup_size_line = next((line for line in stdout.splitlines() if _("Added to the repository:") in line),
                                        None)
                if backup_size_line:
                    data_transferred = backup_size_line.split(_("Added to the repository:"))[1].split(" (")[0].strip()
                    data_stored = backup_size_line.split("(")[1].split(_(" stored"))[0].strip()
                    self.backup_manager.email_body += _(
                        "Files processed: {}, Data transferred: {}, Data stored: {}").format(
                        files_processed, data_transferred, data_stored) + "\n"
                    self.logger.log(
                        _("Files processed: {}, Data transferred: {}, Data stored: {}").format(files_processed,
                                                                                               data_transferred,
                                                                                               data_stored))
                else:
                    self.backup_manager.email_body += _("Files processed: {}, Backup size: unknown").format(
                        files_processed) + "\n"
                    self.logger.log(_("Files processed: {}, Backup size: unknown").format(files_processed))

            self.logger.log(_("Getting Restic Stats"), section=True)
            stats_command = f"restic -r {self.config.RESTIC_REPOSITORY} --password-file {self.config.RESTIC_PASSWORD_FILE} stats --mode restore-size"
            return_code, stdout, stderr = self.command_runner.run(stats_command, verbose=True, timeout=300)
            if return_code == 0:
                uncompressed_size_line = next((line for line in stdout.splitlines() if _("Total Size") in line), None)
                if uncompressed_size_line:
                    uncompressed_size = uncompressed_size_line.split(":")[1].strip()
                    self.backup_manager.email_body += _("Restic repository uncompressed size: {}").format(
                        uncompressed_size) + "\n"
                    self.logger.log(_("Restic repository uncompressed size: {}").format(uncompressed_size))
                else:
                    self.backup_manager.email_body += _("Restic repository uncompressed size: unknown") + "\n"
                    self.logger.log(_("Restic repository uncompressed size: unknown"))
            else:
                error_message = _(
                    "Error: Getting Restic repository stats failed! See log for details at line {}.").format(
                    len(open(self.config.LOG_FILE).readlines()) + 1)
                self.backup_manager.email_body += f"<strong style='color: red;'>{error_message}</strong>\n"
                self.logger.log(f"Error getting Restic repository stats: {stderr}")
                self.backup_manager.error_lines.append(error_message)

            self.logger.log(_("Getting Restic Repository Size"), section=True)
            du_command = f"du -sh {self.config.RESTIC_REPOSITORY}"
            return_code, stdout, stderr = self.command_runner.run(du_command, verbose=True, timeout=300)
            if return_code == 0:
                compressed_size = stdout.split()[0]
                self.backup_manager.email_body += _("Restic repository compressed size: {}").format(
                    compressed_size) + "\n"
                self.logger.log(_("Restic repository compressed size: {}").format(compressed_size))
            else:
                error_message = _(
                    "Error: Getting Restic repository size failed! See log for details at line {}.").format(
                    len(open(self.config.LOG_FILE).readlines()) + 1)
                self.backup_manager.email_body += f"<strong style='color: red;'>{error_message}</strong>\n"
                self.logger.log(f"Error getting Restic repository size: {stderr}")
                self.backup_manager.error_lines.append(error_message)

            self.apply_retention_policy(self.config.RESTIC_REPOSITORY, self.config.RESTIC_PASSWORD_FILE)
