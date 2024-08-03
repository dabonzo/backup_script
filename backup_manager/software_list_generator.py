# backup_manager/software_list_generator.py
import subprocess
from i18n import _
from utils import handle_error

class SoftwareListGenerator:
    """
    Class to generate a list of installed software.
    """
    def __init__(self, config, logger, command_runner, backup_manager):
        """
        Initialize the SoftwareListGenerator class.
        :param config: Configuration object.
        :param logger: Logger object.
        :param command_runner: CommandRunner object.
        :param backup_manager: BackupManager object.
        """
        self.config = config
        self.logger = logger
        self.command_runner = command_runner
        self.backup_manager = backup_manager

    def generate(self):
        """
        Generate the list of installed software.
        """
        self.logger.log(_("Generating List of Installed Software"), section=True)
        self.backup_manager.email_body += "<h2>" + _("Generating List of Installed Software") + "</h2>\n"
        self.logger.log(_("Generating list of installed software..."))

        command = self._get_command_for_distro()
        if command:
            self._run_command(command)
        else:
            self._handle_unsupported_distro()

    def _get_command_for_distro(self):
        """
        Get the command to list installed software based on the distribution.
        :return: Command to list installed software.
        """
        distro = subprocess.run(['/usr/bin/lsb_release', '-is'], capture_output=True, text=True).stdout.strip()
        if distro in ['Ubuntu', 'Debian']:
            return "/usr/bin/dpkg --get-selections"
        elif distro in ['CentOS', 'RedHatEnterpriseServer', 'Fedora']:
            return "rpm -qa"
        return None

    def _run_command(self, command):
        """
        Run the command to list installed software.
        :param command: Command to run.
        """
        return_code, stdout, stderr = self.command_runner.run(f"{command} > {self.config.SOFTWARE_LIST_FILE}", verbose=True)
        if return_code != 0:
            self._handle_error("Error: Generating list of installed software failed!", stderr)
        else:
            self.backup_manager.email_body += _("List of installed software generated successfully.") + "\n"
            self.logger.log(_("List of installed software generated successfully."))

    def _handle_unsupported_distro(self):
        """
        Handle the case where the distribution is not supported.
        """
        error_message = _("Error: Unsupported distribution for generating software list! See log for details at line {}.").format(len(open(self.config.LOG_FILE).readlines()) + 1)
        self.backup_manager.email_body += f"<strong style='color: red;'>{error_message}</strong>\n"
        self.logger.log(_("Error: Unsupported distribution for generating software list!"))
        self.backup_manager.error_lines.append(error_message)
        self.backup_manager.backup_success = False

    def _handle_error(self, message, stderr):
        """
        Handle an error during the backup process.
        :param message: Error message.
        :param stderr: Error output.
        """
        handle_error(message, stderr, self.config, self.logger, self.backup_manager)
