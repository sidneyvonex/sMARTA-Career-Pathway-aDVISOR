from django.core import signing


class TokenExpiredError(Exception):
    pass


class TokenInvalidError(Exception):
    pass


def make_email_verify_token(user_id):
    return signing.dumps({'user_id': user_id}, salt='email-verify')


def load_email_verify_token(token):
    return _load(token, salt='email-verify', max_age=86400)


def make_password_reset_token(user_id):
    return signing.dumps({'user_id': user_id}, salt='password-reset')


def load_password_reset_token(token):
    return _load(token, salt='password-reset', max_age=3600)


def make_invite_token(email, role):
    return signing.dumps({'email': email, 'role': role}, salt='invite')


def load_invite_token(token):
    return _load(token, salt='invite', max_age=172800)


def make_parent_invite_token(student_id, email):
    return signing.dumps({'student_id': student_id, 'email': email}, salt='parent-invite')


def load_parent_invite_token(token):
    return _load(token, salt='parent-invite', max_age=172800)


def _load(token, salt, max_age):
    try:
        return signing.loads(token, salt=salt, max_age=max_age)
    except signing.SignatureExpired:
        raise TokenExpiredError('Token has expired.')
    except signing.BadSignature:
        raise TokenInvalidError('Token is invalid or tampered.')
    except Exception as exc:
        msg = str(exc)
        if 'age' in msg and 'seconds' in msg:
            raise TokenExpiredError('Token has expired.')
        raise TokenInvalidError('Token could not be decoded.')
