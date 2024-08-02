# backup_manager/email_notifier.py
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmailNotifier:
    """
    Class to handle sending notification emails.
    """
    def __init__(self, smtp_server, smtp_port, smtp_username, smtp_password):
        """
        Initialize the EmailNotifier class.
        :param smtp_server: SMTP server address.
        :param smtp_port: SMTP server port.
        :param smtp_username: SMTP username.
        :param smtp_password: SMTP password.
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password

    def send_email(self, subject, to, from_, body_path, attachment_path=None):
        """
        Send an email with optional attachment.
        :param subject: Email subject.
        :param to: Recipient email address.
        :param from_: Sender email address.
        :param body_path: Path to the email body file.
        :param attachment_path: Path to the attachment file.
        """
        with open(body_path, "r") as email_file:
            body = email_file.read()

        msg = MIMEMultipart()
        msg['From'] = from_
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        if attachment_path:
            self._attach_file(msg, attachment_path)

        self._send(msg, from_, to)

    def _attach_file(self, msg, attachment_path):
        """
        Attach a file to the email.
        :param msg: MIMEMultipart message object.
        :param attachment_path: Path to the attachment file.
        """
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(attachment_path)}")
            msg.attach(part)

    def _send(self, msg, from_, to):
        """
        Send the email.
        :param msg: MIMEMultipart message object.
        :param from_: Sender email address.
        :param to: Recipient email address.
        """
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.sendmail(from_, to, msg.as_string())
