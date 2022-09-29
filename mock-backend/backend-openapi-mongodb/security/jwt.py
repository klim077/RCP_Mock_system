import logging
import time
import datetime
from typing import Optional, Tuple

import connexion
# import six
# from werkzeug.exceptions import Unauthorized
import os

from security.scope import validate_scope

from jose import JWTError, jwt

from src import mongoapi2


# Initial delay
time.sleep(10)


def get_docker_secret(secret_name):
    try:
        with open(f'/run/secrets/{secret_name}', 'r') as secret_file:
            return secret_file.read().splitlines()[0]
    except IOError:
        raise


JWT_SECRET = get_docker_secret('JWT_SECRET')
JWT_LIFETIME_SECONDS = int(os.environ['JWT_LIFETIME_SECONDS'])
JWT_REFRESH_LIFETIME_SECONDS = int(os.environ['JWT_REFRESH_LIFETIME_SECONDS'])
JWT_ALGORITHM = os.environ['JWT_ALGORITHM']


"""Logging Levels
|Level   |Numeric value|
|--------|-------------|
|CRITICAL|50           |
|ERROR   |40           |
|WARNING |30           |
|INFO    |20           |
|DEBUG   |10           |
|NOTSET  |0            |
"""

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
# logger.setLevel(logging.WARNING)
# logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
format_str = '%(levelname)s:%(lineno)s:%(message)s'
formatter = logging.Formatter(format_str)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info('Logger ready')


def has_web_headers() -> bool:
    h = connexion.request.headers
    k = 'X-SmartGym-Mode'
    v = 'web'
    result = k in h and h[k] == v
    # logger.debug(f'has_web_headers\n{h}')
    return result


def generate_anti_csrf_token(user_id, anti_csrf):
    timestamp = _current_timestamp()
    payload = {
        "iat": int(timestamp),
        "exp": int(timestamp + JWT_LIFETIME_SECONDS),
        "sub": str(user_id),
        "anti_csrf": str(anti_csrf),
    }

    # Generate token
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token, payload


def generate_access_token(user_id):
    timestamp = _current_timestamp()
    payload = {
        "iat": int(timestamp),
        "exp": int(timestamp + JWT_LIFETIME_SECONDS),
        "sub": str(user_id),
    }

    # Generate token
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token, payload


def generate_refresh_token(user_id):
    # Prepare claims
    timestamp = _current_timestamp()
    payload = {
        "iat": int(timestamp),
        "exp": int(timestamp + JWT_REFRESH_LIFETIME_SECONDS),
        "sub": str(user_id),
        "refresh_token": True,
        # "sub": 'token_refresh',
        # "user_id": user_id,
    }

    # Generate token
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # # Insert token in database
    # mongoapi2.insert_refresh_token(token)

    return token, payload


def refresh_tokens(user_id):
    # Generate new access token
    access_token, access_payload = generate_access_token(user_id)

    # Generate new refresh token
    refresh_token, refresh_payload = generate_refresh_token(user_id)

    # Delete old refresh token
    # Insert new refresh token
    # Delete old access token
    # Insert new access token
    mongoapi2.refresh_tokens(access_payload, refresh_payload)

    # Return new access token and refresh token
    return access_token, refresh_token


def has_valid_anti_csrf(token: str) -> Tuple[bool, Optional[str]]:
    '''Checks if anti-csrf token is valid

    Args:
        token (str): Anti-csrf token
    Returns:
        str: Session token
    '''
    logger.info(f'has_valid_anti_csrf()')

    # Process anti-csrf token
    anti_csrf_token = token
    try:
        claims = jwt.decode(
            anti_csrf_token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except JWTError as e:
        logger.error(e)
        return False, None
    # logger.debug(claims)

    # Guard is [anti_csrf] claim does not exists
    anti_csrf_key = 'anti_csrf'
    if not claims or not claims[anti_csrf_key]:
        logger.debug(f'missing claim {anti_csrf_key} in claims')
        return False, None

    signature_claim = claims[anti_csrf_key]
    # logger.debug(signature_claim)

    # Get session token from cookies
    cookies = connexion.request.cookies
    session_token = cookies.get('sessionKey')
    # logger.debug(session_token)

    # Guard no cookie
    if not session_token:
        logger.debug('no cookie found')
        return False, None

    # Get signature
    try:
        signature = session_token.split('.')[-1]
        logger.debug(signature)
    except Exception as e:
        logger.error(f'unable to process signature {signature}')

    # Check signatures match
    if signature != signature_claim:
        logger.debug(f'signature mismatch {signature} {signature_claim}')
        return False, None

    logger.debug('anti-csrf checks passed')
    return True, session_token


def decode_token(token):
    logger.debug(f'decode_token')

    # Default bearer token as session token
    session_token = token

    # Check header for web session
    if has_web_headers():
        ok, ret = has_valid_anti_csrf(token)
        if ok:
            session_token = ret

    # Decode JWT
    try:
        payload = jwt.decode(
            session_token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
    except JWTError as e:
        logger.error(e)
        return None

    # logger.debug(f'decode_token {payload}')

    # Check scope
    # - [user] defined in claims can only request for [user] data
    user = payload['sub']
    if user and validate_scope(payload):
        return payload

    return None


def get_secret(user, token_info) -> str:
    return '''
    You are user_id {user} and the secret is 'wbevuec'.
    Decoded token claims: {token_info}.
    '''.format(user=user, token_info=token_info)


def _current_timestamp() -> int:
    return int(time.time())
