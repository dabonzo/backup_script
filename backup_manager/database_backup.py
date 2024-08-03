# backup_manager/database_backup.py
import os
import random
from datetime import datetime
from i18n import _

from logger import Logger
from .base_backup import BaseBackup


class DatabaseBackup(BaseBackup):
    """
    Class to handle database backup operations.
    """

    def __init__(self, config, logger, command_runner, backup_manager):
        """
        Initialize the DatabaseBackup class.
        :param config: Configuration object containing backup settings.
        :param logger: Logger object for logging messages.
        :param command_runner: CommandRunner object to execute shell commands.
        :param backup_manager: BackupManager object to manage backup operations.
        """
        super().__init__(config, logger, backup_manager)
        self.command_runner = command_runner

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

        # Simulate failure
        simulate_failure = self.config.SIMULATE_FAILURES
        self.logger.debug_log(f"Simulate failure: {simulate_failure}")

        if simulate_failure:
            self._simulate_failure(db_backup_dir)
            return

        return_code, stdout, stderr = self.command_runner.run(
            f"/usr/bin/mysql -u {self.config.MYSQL_USER} -p{self.config.MYSQL_PASSWORD} -e 'SHOW DATABASES;'")
        if return_code != 0:
            self._handle_error("Error: Cannot list databases!", stderr)
        else:
            self._backup_databases(stdout.split()[1:], db_backup_dir)

    def _simulate_failure(self, db_backup_dir):
        """
        Simulate a failure in the database backup process.
        :param db_backup_dir: Directory where the backup files would be stored.
        """
        non_existent_db = "non_existent_db"
        self.logger.log(_("Simulating failure for database: {}").format(non_existent_db))
        backup_file = os.path.join(db_backup_dir, f"{non_existent_db}.sql.gz")
        return_code, stdout, stderr = self.command_runner.run(
            f"/usr/bin/mysqldump -u {self.config.MYSQL_USER} -p{self.config.MYSQL_PASSWORD} {non_existent_db} | gzip > {backup_file}")
        self._handle_error(f"Error: Database backup failed for {non_existent_db}!", stderr)

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
