# main.py
import argparse
import socket
import os
from i18n import setup_translation, get_translation
from config_loader import ConfigLoader

def main():
    """
    Main function to execute the backup script.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print(f"Changed working directory to: {os.getcwd()}")

    server_name = socket.getfqdn()
    config_loader = ConfigLoader(server_name)
    config = config_loader.config

    print(f"Configured language: {config.LANGUAGE}")
    setup_translation(config.LANGUAGE)

    # Now you can import other modules that use the translation function
    from backup_manager.backup_manager import BackupManager
    from backup_manager.repository_initializer import RepositoryInitializer
    from command_runner import CommandRunner
    from logger import Logger

    parser = argparse.ArgumentParser(description=get_translation()("Backup script for server"))
    parser.add_argument("--verbose", action="store_true", help=get_translation()("Enable verbose output"))
    args = parser.parse_args()

    repository_initializer = RepositoryInitializer(config)
    repository_initializer.ensure_directories()

    logger = Logger(config.LOG_FILE, args.verbose)
    command_runner = CommandRunner(logger)

    repository_initializer.ensure_repository_initialized()

    backup_manager = BackupManager(config, logger, command_runner)
    backup_manager.backup()

if __name__ == "__main__":
    main()
