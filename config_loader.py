# config_loader.py
import importlib.util
import os
from i18n import _

class ConfigLoader:
    """
    Class to load configuration dynamically based on server name.
    """
    def __init__(self, server_name):
        """
        Initialize the ConfigLoader class.
        :param server_name: Fully qualified domain name of the server.
        """
        self.server_name = server_name
        self.config = self.load_config()

    def load_config(self):
        """
        Load the configuration file.
        :return: Configuration module.
        """
        config_path = f'/root/backup_config_{self.server_name}.py'
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                _("Configuration file {} does not exist. Ensure the correct config file is present.").format(config_path))

        spec = importlib.util.spec_from_file_location("config", config_path)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        if self.server_name != config.SERVER_NAME:
            raise EnvironmentError(
                _("The configuration file {} is not intended for this server ({}).").format(config_path, self.server_name))
        return config
