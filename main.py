import argparse
import socket

from backup_manager.backup_manager import BackupManager
from backup_manager.repository_initializer import RepositoryInitializer
from command_runner import CommandRunner
from config_loader import ConfigLoader
from i18n_setup import setup_i18n, _
from logger import Logger


def main():
    # Determine the server's fully qualified domain name (FQDN)
    server_name = socket.getfqdn()
    # Load the configuration file dynamically based on the server's FQDN
    config_loader = ConfigLoader(server_name)
    config = config_loader.config

    # Setup internationalization
    setup_i18n(config.LANGUAGE)

    # Setup argument parser
    parser = argparse.ArgumentParser(description=_("Backup script for server"))
    parser.add_argument("--verbose", action="store_true", help=_("Enable verbose output"))
    args = parser.parse_args()

    # Initialize repository and ensure it is set up correctly
    repository_initializer = RepositoryInitializer(config)
    repository_initializer.ensure_directories()

    # Initialize logger and command runner
    logger = Logger(config.LOG_FILE, args.verbose)
    command_runner = CommandRunner(logger)

    # Ensure repository is initialized
    repository_initializer.ensure_repository_initialized()

    # Initialize and run the backup manager
    backup_manager = BackupManager(config, logger, command_runner)
    backup_manager.backup()


if __name__ == "__main__":
    main()
