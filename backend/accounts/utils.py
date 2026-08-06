import secrets
import string


def _temporary_password():
    """Return a readable password with a mix of character classes."""
    characters = string.ascii_letters + string.digits
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        *[secrets.choice(characters) for _ in range(9)],
    ]
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)
