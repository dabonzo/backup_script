# backup_manager/repository_initializer.py
import os
import secrets
import string
import subprocess

class RepositoryInitializer:
    """
    Class to handle Restic repository initialization and setup.
    """
    def __init__(self, config):
        """
        Initialize the RepositoryInitializer class.
        :param config: Configuration object.
        """
        self.config = config

    def ensure_directories(self):
        """
        Ensure necessary directories exist, creating them if necessary.
        """
        directories = [self.config.BASE_BACKUP_DIR, self.config.MYSQL_BACKUP_DIR, self.config.LOG_DIR]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

    def generate_password(self):
        """
        Generate a secure password for the Restic repository.
        """
        alphabet = string.ascii_letters + string.digits + '-_'
        while True:
            restic_password = ''.join(secrets.choice(alphabet) for _ in range(20))
            if sum(c.islower() for c in restic_password) >= 4 and sum(c.isupper() for c in restic_password) >= 4 and sum(c.isdigit() for c in restic_password) >= 4 and sum(c in '-_' for c in restic_password) >= 2:
                break
        with open(self.config.RESTIC_PASSWORD_FILE, "w") as pw_file:
            pw_file.write(restic_password)
        os.chmod(self.config.RESTIC_PASSWORD_FILE, 0o600)

    def initialize_repository(self):
        """
        Initialize the Restic repository.
        """
        init_command = f"restic -r {self.config.RESTIC_REPOSITORY} --password-file {self.config.RESTIC_PASSWORD_FILE} init"
        result = subprocess.run(init_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print("Restic repository initialized successfully.")
        else:
            print(f"Error initializing Restic repository: {result.stderr}")
            raise RuntimeError("Failed to initialize Restic repository")

    def ensure_repository_initialized(self):
        """
        Ensure the Restic repository is initialized.
        """
        if not os.path.isdir(os.path.join(self.config.RESTIC_REPOSITORY, "data")):
            self.generate_password()
            self.initialize_repository()
