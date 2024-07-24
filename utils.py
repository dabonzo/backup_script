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
