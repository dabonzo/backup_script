import os


class SizeCalculator:
    def __init__(self, config, logger, command_runner, backup_manager):
        self.config = config
        self.logger = logger
        self.command_runner = command_runner
        self.backup_manager = backup_manager

    @staticmethod
    def get_dir_size(directory):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    def calculate(self):
        self.logger.log(_("Calculating Total Size of Backup Folder"), section=True)
        backup_dir_size = self.get_dir_size(self.config.BASE_BACKUP_DIR)
        size_in_mb = backup_dir_size / (1024 * 1024)

        size_message = _("Total size of backup folder: {:.2f} MB").format(size_in_mb)

        self.backup_manager.email_body += f"<h2>{_('Total Size of Backup Folder')}</h2>\n{size_message}\n"
        self.logger.log(size_message)

