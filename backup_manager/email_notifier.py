# backup_manager/email_notifier.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class EmailNotifier:
    """
    Class to handle sending emails.
    """
    def __init__(self, smtp_server, smtp_port, smtp_username, smtp_password):
        """
        Initialize the EmailNotifier class.
        :param smtp_server: SMTP server address.
        :param smtp_port: SMTP server port.
        :param smtp_username: SMTP server username.
        :param smtp_password: SMTP server password.
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password

    def send_email(self, subject, to_addresses, from_address, body_path, attachment_path=None):
        """
        Send an email with optional attachment.
        :param subject: Email subject.
        :param to_addresses: List of recipient email addresses.
        :param from_address: Sender email address.
        :param body_path: Path to the email body file.
        :param attachment_path: Path to the attachment file.
        """
        # Ensure to_addresses is a list and correctly formatted
        if isinstance(to_addresses, str):
            to_addresses = [to_addresses]
        to_addresses_list = to_addresses  # Preserve the list for the actual sending
        to_addresses = ", ".join(to_addresses)  # Join for the 'To' header

        # Read the email body from the file
        with open(body_path, "r") as email_file:
            body = email_file.read()

        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = from_address
        msg['To'] = to_addresses
        msg['Subject'] = subject

        # Attach the email body
        msg.attach(MIMEText(body, 'html'))

        # Attach a file if specified
        if attachment_path:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(attachment_path)}")
                msg.attach(part)

        # Send the email
        self._send(msg, from_address, to_addresses_list)

    def _send(self, msg, from_address, to_addresses):
        """
        Send the email using the SMTP server.
        :param msg: MIMEMultipart message object.
        :param from_address: Sender email address.
        :param to_addresses: List of recipient email addresses.
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(from_address, to_addresses, msg.as_string())
        except smtplib.SMTPRecipientsRefused as e:
            raise RuntimeError(f"Failed to send email: {e.recipients}")
        except smtplib.SMTPException as e:
            raise RuntimeError(f"SMTP error occurred: {e}")
