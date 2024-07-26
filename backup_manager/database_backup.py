import os
from datetime import datetime
from i18n import _

class DatabaseBackup:
    def __init__(self, config, logger, command_runner, backup_manager):
        self.config = config
        self.logger = logger
        self.command_runner = command_runner
        self.backup_manager = backup_manager

    def backup(self):
        self.logger.log(_("Database Backup"), section=True)
        self.backup_manager.email_body += "<h2>" + _("Database Backup") + "</h2>\n"
        self.logger.log(_("Starting database backup..."))
        backup_date = datetime.now().strftime("%Y-%m-%d")
        db_backup_dir = os.path.join(self.config.MYSQL_BACKUP_DIR, backup_date)
        os.makedirs(db_backup_dir, exist_ok=True)
        return_code, stdout, stderr = self.command_runner.run(
            f"mysql -u {self.config.MYSQL_USER} -p{self.config.MYSQL_PASSWORD} -e 'SHOW DATABASES;'")
        if return_code != 0:
            error_message = _("Error: Cannot list databases! See log for details at line {}.").format(
                len(open(self.config.LOG_FILE).readlines()) + 1)
            self.backup_manager.email_body += f"<strong style='color: red;'>{error_message}</strong><br>\n"
            self.logger.log(f"Error: Cannot list databases! {stderr}")
            self.backup_manager.error_lines.append(error_message)
            self.backup_manager.backup_success = False
        else:
            databases = stdout.split()[1:]
            exclude_dbs = {"information_schema", "performance_schema"}
            for db in databases:
                if db in exclude_dbs:
                    self.logger.log(_("Skipping backup for database: {}").format(db))
                    continue
                backup_file = os.path.join(db_backup_dir, f"{db}.sql.gz")
                return_code, stdout, stderr = self.command_runner.run(
                    f"mysqldump -u {self.config.MYSQL_USER} -p{self.config.MYSQL_PASSWORD} {db} | gzip > {backup_file}")
                if return_code != 0 or _("mysqldump: Got error:") in stderr:
                    error_message = _("Error: Database backup failed for {}! See log for details at line {}.").format(
                        db, len(open(self.config.LOG_FILE).readlines()) + 1)
                    self.backup_manager.email_body += f"<strong style='color: red;'>{error_message}</strong><br>\n"
                    self.logger.log(f"Error: Database backup failed for {db}! {stderr}")
                    self.backup_manager.error_lines.append(error_message)
                    self.backup_manager.backup_success = False
                else:
                    self.backup_manager.email_body += _("Database {} backed up successfully.").format(db) + "<br>\n"
                    self.logger.log(_("Database {} backed up successfully to {}.").format(db, backup_file))
