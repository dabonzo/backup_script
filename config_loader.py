import importlib.util
import os


class ConfigLoader:
    def __init__(self, server_name):
        self.server_name = server_name
        self.config = self.load_config()

    def load_config(self):
        config_path = f'/root/backup_config_{self.server_name}.py'
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                _("Configuration file {} does not exist. Ensure the correct config file is present.").format(
                    config_path))

        spec = importlib.util.spec_from_file_location("config", config_path)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        if self.server_name != config.SERVER_NAME:
            raise EnvironmentError(
                _("The configuration file {} is not intended for this server ({}).").format(config_path,
                                                                                            self.server_name))
        return config
