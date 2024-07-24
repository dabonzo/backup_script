# Backup Script

## Overview
This script performs backups of various services, databases, and directories, and stores the backups in a Restic repository. It also handles logging and sends notifications via email. The script is designed to be modular and maintainable, with support for internationalization and error simulation for testing purposes.

## Features
- Backup MySQL databases
- Backup directories and services
- Manage Restic repository
- Send email notifications
- Internationalization support
- Simulate failures for testing

## File Structure

```plaintext
backup/
├── script/
│   ├── command_runner.py
│   ├── config_loader.py
│   ├── i18n_setup.py
│   ├── main.py
│   ├── utils.py
│   ├── backup_manager/
│   │   ├── __init__.py
│   │   ├── backup_manager.py
│   │   ├── database_backup.py
│   │   ├── restic_backup.py
│   │   ├── software_list_generator.py
│   │   ├── size_calculator.py
│   │   ├── log_cleaner.py
│   │   ├── email_notifier.py
│   │   └── repository_initializer.py
│   ├── locales/
│   │   ├── backup.pot
│   │   └── en/
│   │       └── LC_MESSAGES/
│   │           └── backup.mo
```
## Configuration

The configuration file should be placed in `/root` with the name format `backup_config_<FQDN>.py`. Example configuration variables include:
``` python
import socket
from datetime import datetime

SERVER_NAME = socket.getfqdn()
BASE_BACKUP_DIR = f"/backup/{SERVER_NAME}"
MYSQL_USER = "dbuser"
MYSQL_PASSWORD = "yourpassword"
MYSQL_BACKUP_DIR = f"{BASE_BACKUP_DIR}/db-backups"
RESTIC_REPOSITORY = f"{BASE_BACKUP_DIR}/restic"
RESTIC_PASSWORD_FILE = f"{BASE_BACKUP_DIR}/restic-{SERVER_NAME}-pw"
EMAIL_TO = "your-email@example.com"
EMAIL_FROM = "backup@example.com"
EMAIL_BODY_PATH = "/tmp/backup_summary.html"
LOG_DIR = f"{BASE_BACKUP_DIR}/logs"
LOG_FILE = f"{LOG_DIR}/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}-backup-log.txt"
SOFTWARE_LIST_FILE = f"{BASE_BACKUP_DIR}/software-installed.txt"
RETENTION_DAYS = 30
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-smtp-username"
SMTP_PASSWORD = "your-smtp-password"
LANGUAGE = 'en'
SIMULATE_FAILURES = False
DEFAULT_PATHS = ["/etc", "/var/spool/cron", "/var/backups"]
SERVICE_CONFIGS = {
    "apache2": ["/var/www"],
    "nginx": ["/var/www"],
    "postfix": ["/var/vmail"],
    "bind9": ["/var/named"]
}
```
## Usage

Run the script using:

``` shell
python3 main.py --verbose
```
## File Descriptions

### command_runner.py

Runs shell commands with logging.

### config_loader.py

Loads configuration dynamically based on the server's FQDN.

### i18n_setup.py

Sets up internationalization.

### main.py

Main entry point of the script.

### utils.py

Utility functions used across the project.

### backup_manager/

#### **init**.py

Initializes the backup manager package.

#### backup_manager.py

Manages the overall backup process.

#### database_backup.py

Handles database backups.

#### restic_backup.py

Handles Restic backups.

#### software_list_generator.py

Generates a list of installed software.

#### size_calculator.py

Calculates the size of backup directories.

#### log_cleaner.py

Cleans old logs.

#### email_notifier.py

Sends email notifications.

#### repository_initializer.py

Ensures necessary directories are set up and initializes the Restic repository if not present.

### locales/

Contains translation files for internationalization.

## Tasks for the Assistant

- Add comprehensive documentation for all files, including explanations of their purpose, design, and implementation.
- Refactor code to ensure it adheres to DRY and SOLID principles.
- Implement internationalization support using gettext.
- Ensure the backup process handles errors gracefully and sends detailed email notifications.
- Maintain a clean code structure and modular design for easy maintenance and testing.

Use the provided project structure and functionality as the basis for further development and improvements.
``` text
This `README.md` file provides an overview of the project, explains its features, details the file structure and configuration, and includes usage instructions. It also describes the purpose and functionality of each file in the project.
```
