# backup_manager/database_backup.py
import os
from datetime import datetime

from i18n import _

class DatabaseBackup:
    """
    Class to handle database backup operations.
    """
    def __init__(self, config, logger, command_runner, backup_manager):
        """
        Initialize the DatabaseBackup class.
        :param config: Configuration object.
        :param logger: Logger object.
        :param command_runner: CommandRunner object.
        :param backup_manager: BackupManager object.
        """
        self.config = config
        self.logger = logger
        self.command_runner = command_runner
        self.backup_manager = backup_manager

    def backup(self):
        """
        Perform the database backup operation.
        """
        self.logger.log(_("Database Backup"), section=True)
        self.backup_manager.email_body += "<h2>" + _("Database Backup") + "</h2>\n"
        self.logger.log(_("Starting database backup..."))
        backup_date = datetime.now().strftime("%Y-%m-%d")
        db_backup_dir = os.path.join(self.config.MYSQL_BACKUP_DIR, backup_date)
        os.makedirs(db_backup_dir, exist_ok=True)
        return_code, stdout, stderr = self.command_runner.run(
            f"/usr/bin/mysql -u {self.config.MYSQL_USER} -p{self.config.MYSQL_PASSWORD} -e 'SHOW DATABASES;'")
        if return_code != 0:
            self._handle_error("Error: Cannot list databases!", stderr)
        else:
            self._backup_databases(stdout.split()[1:], db_backup_dir)

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

    def _backup_databases(self, databases, db_backup_dir):
        """
        Backup the databases.
        :param databases: List of databases to backup.
        :param db_backup_dir: Directory to store the backup files.
        """
        exclude_dbs = {"information_schema", "performance_schema"}
        for db in databases:
            if db in exclude_dbs:
                self.logger.log(_("Skipping backup for database: {}").format(db))
                continue
            backup_file = os.path.join(db_backup_dir, f"{db}.sql.gz")
            return_code, stdout, stderr = self.command_runner.run(
                f"/usr/bin/mysqldump -u {self.config.MYSQL_USER} -p{self.config.MYSQL_PASSWORD} {db} | gzip > {backup_file}")
            if return_code != 0 or _("mysqldump: Got error:") in stderr:
                self._handle_error(f"Error: Database backup failed for {db}!", stderr)
            else:
                self.backup_manager.email_body += _("Database {} backed up successfully.").format(db) + "<br>\n"
                self.logger.log(_("Database {} backed up successfully to {}.").format(db, backup_file))
