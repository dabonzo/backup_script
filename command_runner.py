# command_runner.py

import subprocess
from i18n import _

class CommandRunner:
    """
    Class to run shell commands and log the output.
    """
    def __init__(self, logger):
        """
        Initialize the CommandRunner class.
        :param logger: Logger object for logging messages.
        """
        self.logger = logger

    def run(self, command, verbose=False, timeout=600):
        """
        Run a shell command.
        :param command: The command to run.
        :param verbose: Flag to enable verbose output.
        :param timeout: Timeout for the command execution.
        :return: Tuple containing return code, stdout, and stderr.
        """
        self.logger.log(_("Running command: {}").format(command))
        try:
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            self.logger.log(_("Command timed out: {}").format(command))
            return 1, "", "TimeoutExpired"
        if verbose or self.logger.verbose:
            print(result.stdout)
            print(result.stderr)
        return result.returncode, result.stdout, result.stderr
