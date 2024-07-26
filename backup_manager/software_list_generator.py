import subprocess

from i18n import _


class SoftwareListGenerator:
    def __init__(self, config, logger, command_runner, backup_manager):
        self.config = config
        self.logger = logger
        self.command_runner = command_runner
        self.backup_manager = backup_manager

    def generate(self):
        self.logger.log(_("Generating List of Installed Software"), section=True)
        self.backup_manager.email_body += "<h2>" + _("Generating List of Installed Software") + "</h2>\n"
        self.logger.log(_("Generating list of installed software..."))
        distro = subprocess.run(['lsb_release', '-is'], capture_output=True, text=True).stdout.strip()
        if distro in ['Ubuntu', 'Debian']:
            command = "dpkg --get-selections"
        elif distro in ['CentOS', 'RedHatEnterpriseServer', 'Fedora']:
            command = "rpm -qa"
        else:
            command = None

        if command:
            return_code, stdout, stderr = self.command_runner.run(f"{command} > {self.config.SOFTWARE_LIST_FILE}",
                                                                  verbose=True)
            if return_code != 0:
                error_message = _(
                    "Error: Generating list of installed software failed! See log for details at line {}.").format(
                    len(open(self.config.LOG_FILE).readlines()) + 1)
                self.backup_manager.email_body += f"<strong style='color: red;'>{error_message}</strong>\n"
                self.logger.log(f"Error: Generating list of installed software failed! {stderr}")
                self.backup_manager.error_lines.append(error_message)
                self.backup_manager.backup_success = False
            else:
                self.backup_manager.email_body += _("List of installed software generated successfully.") + "\n"
                self.logger.log(_("List of installed software generated successfully."))
        else:
            error_message = _(
                "Error: Unsupported distribution for generating software list! See log for details at line {}.").format(
                len(open(self.config.LOG_FILE).readlines()) + 1)
            self.backup_manager.email_body += f"<strong style='color: red;'>{error_message}</strong>\n"
            self.logger.log(_("Error: Unsupported distribution for generating software list!"))
            self.backup_manager.error_lines.append(error_message)
            self.backup_manager.backup_success = False
