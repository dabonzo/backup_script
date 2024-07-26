import secrets
import string


def generate_secure_password(length=20):
    """
    Generates a secure password containing at least:
    - 4 lowercase letters
    - 4 uppercase letters
    - 4 digits
    - 2 special characters (-_)
    """
    alphabet = string.ascii_letters + string.digits + '-_'
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (sum(c.islower() for c in password) >= 4 and
                sum(c.isupper() for c in password) >= 4 and
                sum(c.isdigit() for c in password) >= 4 and
                sum(c in '-_' for c in password) >= 2):
            return password
# utils.py
def format_duration(duration):
    total_seconds = int(duration.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds} seconds"
    elif total_seconds < 3600:
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes} minutes {seconds} seconds"
    else:
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours} hours {minutes} minutes {seconds}"


def log_and_email(backup_manager, logger, message, section=False, error=False):
    if section:
        formatted_message = f"<h2>{message}</h2>"
    else:
        formatted_message = f"<p>{message}</p>"

    if error:
        formatted_message = f"<strong style='color: red;'>{formatted_message}</strong><br>"
        backup_manager.error_lines.append(formatted_message)
        backup_manager.backup_success = False

    backup_manager.email_body += formatted_message + "\n"
    logger.log(message)