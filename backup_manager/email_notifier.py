import gettext
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_ = gettext.gettext


class EmailNotifier:
    def __init__(self, smtp_server, smtp_port, smtp_username, smtp_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password

    def send_email(self, subject, to, from_, body_path, attachment_path=None):
        with open(body_path, "r") as email_file:
            body = email_file.read()

        msg = MIMEMultipart()
        msg['From'] = from_
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        if attachment_path:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(attachment_path)}")
                msg.attach(part)

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.sendmail(from_, to, msg.as_string())
