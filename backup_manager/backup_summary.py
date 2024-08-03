# backup_summary.py
import os
import sys
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import socket
import importlib.util

def load_config(server_name):
    """
    Load the configuration module based on the server's FQDN.
    :param server_name: The server's fully qualified domain name (FQDN).
    :return: Configuration object.
    """
    config_path = f'/root/backup_config_{server_name}.py'
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Configuration file {config_path} does not exist. Ensure the correct config file is present.")

    spec = importlib.util.spec_from_file_location("config", config_path)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)
    return config

def format_time_without_seconds(time_str):
    """
    Format the time string to remove seconds.
    :param time_str: The original time string with seconds.
    :return: Formatted time string without seconds.
    """
    return time_str.rsplit(':', 1)[0]

def send_summary_email(status_files, config):
    """
    Send a summary email with the backup status of all servers.
    :param status_files: List of status files.
    :param config: Configuration object.
    """
    print("Sending summary email")  # Debug print

    summary_body = """
    <html>
    <body>
    <h2>Backup Summary</h2>
    <table border='1'>
    <tr>
        <th>Server</th>
        <th>Status</th>
        <th>Start Time</th>
        <th>End Time</th>
        <th>Duration</th>
    </tr>
    """
    for status_file in status_files:
        with open(status_file, "r") as file:
            content = file.read()
            server_name = re.search(r'Server:\s*(.*)', content).group(1)
            status = re.search(r'Status:\s*(.*)', content).group(1)
            start_time = format_time_without_seconds(re.search(r'Start Time:\s*(.*)', content).group(1))
            end_time = format_time_without_seconds(re.search(r'End Time:\s*(.*)', content).group(1))
            duration = re.search(r'Duration:\s*(.*)', content).group(1)

            row_color = "style='color: red;'" if status == "Failed" else ""
            summary_body += f"""
            <tr {row_color}>
                <td>{server_name}</td>
                <td>{status}</td>
                <td>{start_time}</td>
                <td>{end_time}</td>
                <td>{duration}</td>
            </tr>
            """
    summary_body += """
    </table>
    <p>Note: Separate emails were sent for failed backups.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = config.EMAIL_FROM
    msg['To'] = ", ".join(config.SUMMARY_EMAIL_TO)
    msg['Subject'] = "Backup Summary"

    msg.attach(MIMEText(summary_body, 'html'))

    with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.sendmail(config.EMAIL_FROM, config.SUMMARY_EMAIL_TO, msg.as_string())

def main():
    """
    Main function to read backup status files and send a summary email.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    server_name = socket.getfqdn()
    config = load_config(server_name)

    status_files = [os.path.join(config.STATUS_FILE_DIR, f) for f in os.listdir(config.STATUS_FILE_DIR) if f.startswith("backup_status_")]

    send_summary_email(status_files, config)

    # Delete status files after sending the summary email
    for status_file in status_files:
        os.remove(status_file)

if __name__ == "__main__":
    main()
