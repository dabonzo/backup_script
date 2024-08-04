# utils.py
import os
import secrets
import string
from i18n import _

def generate_secure_password(length=20):
    """
    Generates a secure password.
    :param length: Length of the password.
    :return: Secure password.
    """
    alphabet = string.ascii_letters + string.digits + '-_'
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if sum(c.islower() for c in password) >= 4 and sum(c.isupper() for c in password) >= 4 and sum(c.isdigit() for c in password) >= 4 and sum(c in '-_' for c in password) >= 2:
            return password

def format_duration(duration):
    """
    Format a duration as a human-readable string.
    :param duration: Duration to format.
    :return: Formatted duration string.
    """
    total_seconds = int(duration.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds} seconds"
    elif total_seconds < 3600:
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes} minutes {seconds} seconds"
    else:
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours} hours {minutes} minutes {seconds}"

def log_and_email(backup_manager, logger, message, section=False, error=False):
    """
    Log a message and add it to the email body.
    :param backup_manager: BackupManager instance.
    :param logger: Logger instance.
    :param message: Message to log and email.
    :param section: Whether to format the message as a section header.
    :param error: Whether the message is an error.
    """
    if section:
        formatted_message = f"<h2>{message}</h2>"
    else:
        formatted_message = f"<p>{message}</p>"

    if error:
        formatted_message = f"<strong style='color: red;'>{formatted_message}</strong><br>"
        backup_manager.error_lines.append(formatted_message)
        backup_manager.backup_success = False

    backup_manager.email_body += formatted_message + "\n"
    logger.log(message)

def is_restic_locked(repository, password_file, command_runner, logger):
    """
    Check if the Restic repository is locked.
    :param repository: Restic repository path.
    :param password_file: Path to the Restic password file.
    :param command_runner: CommandRunner instance.
    :param logger: Logger instance.
    :return: Boolean indicating if the repository is locked.
    """
    check_lock_command = f"restic -r {repository} --password-file {password_file} list locks"
    return_code, stdout, stderr = command_runner.run(check_lock_command, verbose=True)
    if return_code != 0:
        logger.log(f"Error checking locks for repository {repository}: {stderr}")
        return False
    if stdout:
        logger.log(f"Restic repository {repository} is locked.")
        return True
    logger.log(f"Restic repository {repository} is not locked.")
    return False

def get_dir_size(directory):
    """
    Get the total size of a directory.
    :param directory: Directory path.
    :return: Total size of the directory in bytes.
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

class BackupSizeCalculator:
    """
    Class to calculate the size of backups.
    """
    def __init__(self, config, command_runner, logger):
        """
        Initialize the BackupSizeCalculator class.
        :param config: Configuration object.
        :param command_runner: CommandRunner instance.
        :param logger: Logger instance.
        """
        self.config = config
        self.command_runner = command_runner
        self.logger = logger

    def extract_backup_size(self, backup_size_line):
        """
        Extract the size of the backup from the output line.
        :param backup_size_line: Line containing backup size information.
        :return: Tuple containing data transferred and data stored.
        """
        data_transferred = backup_size_line.split("Added to the repository:")[1].split(" (")[0].strip()
        data_stored = backup_size_line.split("(")[1].split(" stored")[0].strip()
        return data_transferred, data_stored

    def get_uncompressed_size(self):
        """
        Get the uncompressed size of the backup.
        :return: Uncompressed size of the backup.
        """
        stats_command = f"restic -r {self.config.RESTIC_REPOSITORY} --password-file {self.config.RESTIC_PASSWORD_FILE} stats --mode restore-size"
        return_code, stdout, stderr = self.command_runner.run(stats_command, verbose=True, timeout=3600)
        if return_code == 0:
            uncompressed_size_line = next((line for line in stdout.splitlines() if "Total Size" in line), None)
            if uncompressed_size_line:
                return uncompressed_size_line.split(":")[1].strip()
        return _("unknown")

    def get_compressed_size(self):
        """
        Get the compressed size of the backup.
        :return: Compressed size of the backup.
        """
        du_command = f"du -sh {self.config.RESTIC_REPOSITORY}"
        return_code, stdout, stderr = self.command_runner.run(du_command, verbose=True, timeout=3600)
        if return_code == 0:
            return stdout.split()[0]
        return _("unknown")

    def calculate_total_backup_size(self):
        """
        Calculate the total size of the backup directory.
        :return: Total size of the backup directory in MB.
        """
        backup_dir_size = get_dir_size(self.config.BASE_BACKUP_DIR)
        size_in_mb = backup_dir_size / (1024 * 1024)
        return size_in_mb

def handle_error(message, stderr, config, logger, backup_manager):
    """
    Handle an error during the backup process.
    :param message: Error message.
    :param stderr: Error output.
    :param config: Configuration object.
    :param logger: Logger object.
    :param backup_manager: BackupManager object.
    """
    error_message = _(message + " See log for details at line {}.").format(len(open(config.LOG_FILE).readlines()) + 1)
    backup_manager.email_body += f"<strong style='color: red;'>{error_message}</strong><br>\n"
    logger.log(f"{message} {stderr}")
    backup_manager.error_lines.append(error_message)
    backup_manager.backup_success = False