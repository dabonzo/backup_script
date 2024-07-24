import argparse
import socket

from config_loader import ConfigLoader
from logger import Logger
from command_runner import CommandRunner
from backup_manager.backup_manager import BackupManager
from i18n_setup import setup_i18n, _


def main():
    server_name = socket.getfqdn()
    config_loader = ConfigLoader(server_name)
    config = config_loader.config

    # Setup internationalization
    setup_i18n(config.LANGUAGE)

    parser = argparse.ArgumentParser(description=_("Backup script for server"))
    parser.add_argument("--verbose", action="store_true", help=_("Enable verbose output"))
    args = parser.parse_args()

    logger = Logger(config.LOG_FILE, args.verbose)
    command_runner = CommandRunner(logger)

    backup_manager = BackupManager(config, logger, command_runner)
    backup_manager.backup()


if __name__ == "__main__":
    main()
