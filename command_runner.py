import subprocess
from i18n import _




class CommandRunner:
    def __init__(self, logger):
        self.logger = logger

    def run(self, command, verbose=False, timeout=600):
        self.logger.log(_("Running command: {}").format(command))
        try:
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                    timeout=timeout)
        except subprocess.TimeoutExpired:
            self.logger.log(_("Command timed out: {}").format(command))
            return 1, "", "TimeoutExpired"
        if verbose or self.logger.verbose:
            print(result.stdout)
            print(result.stderr)
        return result.returncode, result.stdout, result.stderr
