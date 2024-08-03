# main.py
import argparse
import socket
import os
from i18n import setup_translation, get_translation
from config_loader import ConfigLoader
from logger import Logger

def log_config_settings(config):
    """
    Log all configuration settings using the debug logger.
    :param config: Configuration object containing settings.
    """
    logger = Logger.get_instance()
    for attribute in dir(config):
        if not attribute.startswith("__") and not callable(getattr(config, attribute)):
            logger.debug_log(f"{attribute}: {getattr(config, attribute)}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    server_name = socket.getfqdn()
    config = ConfigLoader(server_name).config

    parser = argparse.ArgumentParser(description="Backup script for server")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--simulate-failures", action="store_true", help="Simulate failures in the backup process")
    args = parser.parse_args()

    # Initialize the logger singleton
    logger = Logger.get_instance(config.LOG_FILE, args.verbose, args.debug)

    if args.debug:
        log_config_settings(config)

    logger.debug_log(f"Changed working directory to: {os.getcwd()}")
    logger.debug_log(f"Configured language: {config.LANGUAGE}")

    # Override config value with command-line argument if provided
    if args.simulate_failures:
        config.SIMULATE_FAILURES = True

    setup_translation(config.LANGUAGE)

    from backup_manager.backup_manager import BackupManager
    from backup_manager.repository_initializer import RepositoryInitializer
    from command_runner import CommandRunner

    repository_initializer = RepositoryInitializer(config)
    repository_initializer.ensure_directories()

    command_runner = CommandRunner(logger)

    repository_initializer.ensure_repository_initialized()

    backup_manager = BackupManager(config, logger, command_runner)
    backup_manager.backup()

if __name__ == "__main__":
    main()
