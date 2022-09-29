from base64 import b64encode, b64decode
from datetime import datetime, timedelta
import json
import logging
import os
import re
import uuid

import connexion
from flask import request, jsonify, make_response
import redis
import requests

from src import mongoapi2
from models.account import validate_user
import routes.twilio_services as otp_services
from security.aes import encrypt, decrypt
from security.jwt import (
    generate_access_token,
    generate_refresh_token,
    decode_token,
    refresh_tokens,
    generate_anti_csrf_token
)
from security.scope import validate_scope


# Constants
ID_KEY = 'activesg_id'


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


class RDB:
    def __init__(self, host: str = 'redis', port: int = 6379, limit: int = 10):
        self.host = host
        self.port = port
        self.limit = limit

    def __enter__(self):
        import redis

        logger.info(f'Connecting to redis at {self.host}:{self.port}')
        connected = False
        attempts = 0
        while not connected and self.limit - attempts > 0:
            attempts += 1
            logger.info(f'Attempt {attempts} of {self.limit}')
            try:
                self.client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    decode_responses=True,
                )
                self.client.ping()
                connected = True
                logger.info(f'Connected to redis')
                return self.client
            except Exception as e:
                logger.error(e)
                time.sleep(1)

        raise ConnectionError('Connection error from RDB')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.connection_pool.disconnect()
        del self.client


def has_web_headers() -> bool:
    h = connexion.request.headers
    k = 'X-SmartGym-Mode'
    v = 'web'
    result = k in h and h[k] == v
    logger.debug(f'has_web_headers\n{h}')
    return result


def is_truthy(query: str) -> bool:
    truthy_strings = ['true', 'yes', 'y', '1']
    if query.lower() in truthy_strings:
        return True

    return False


def is_mock() -> bool:
    mock = os.environ['MOCK_TWILIO']
    result = is_truthy(query=mock)
    logger.debug(f'is_mock "{mock}" is {result}')
    return result


# Sanity check
logger.info(f'Sanity check: MOCK is {is_mock()}')


def basic_auth(username, password, required_scopes=None):
    '''Login Endpoint'''
    # print('basic_auth', username, password, flush=True)

    user = mongoapi2.login(username, password)

    if user:
        # Prepare response
        info = {
            # 'sub' is passed as 'user' to handler function
            'sub': user['user_id']
        }
        return info
    else:
        logger.error("Authentication Failed")
        return None


def active_sg_auth(activeSgId, required_scopes=None):
    logger.info("active_sg_auth")
    user = mongoapi2.loginWithActiveSgQR(activeSgId)

    if user:
        # Prepare response
        info = {
            'sub': user['user_id']
        }
        logger.debug(f'successful active_sg_auth')
        return info

    return None


def extract_activesg_id_token(token: str) -> tuple[bool, str]:
    # Decode from base64
    decoded = b64decode(token)

    # Decrypt
    decrypted = decrypt(decoded)

    # Remove leading 0's
    stripped = decrypted.lstrip('0')

    # Deserialized to object
    deserialized = json.loads(stripped)

    # Extract values
    activesg_id = deserialized[ID_KEY]
    token = deserialized['token']

    return activesg_id, token


def validate_activesg_id_token(activesg_id: str, token: str) -> bool:
    # Retrieve stored token from redis
    name = f'activesgids:{activesg_id}'
    with RDB() as r:
        stored_token = r.get(name)

    # Check for expired token
    if not stored_token:
        return False

    # Check if token is equal
    if token != stored_token:
        return False

    return True


def activesg_id_token(token, required_scopes=None):
    logger.info("activesg_id_token() start")

    # Check if token is valid
    activesg_id, token = extract_activesg_id_token(token)
    if not activesg_id or not token:
        return None

    # Validate token
    if not validate_activesg_id_token(activesg_id, token):
        return None

    # Get user info from mongodb
    user = mongoapi2.loginWithActiveSgQR(activesg_id)
    if not user:
        return None

    # Prepare response
    info = {
        'sub': user['user_id']
    }

    return info


def validate_otp(otp: str) -> bool:
    # logger.debug(f'validate_otp {otp}')

    otp_pattern = '^[0-9]{6}$'
    pattern_check = re.match(otp_pattern, otp)

    if not pattern_check:
        return False

    return True


def otp_auth(otp, required_scopes=None):
    # logger.debug(f'otp_auth {otp}')

    if not validate_otp(otp=otp):
        return None

    body = connexion.request.json
    phone_number = body['phone_number']

    # Convert to E164
    number = mongoapi2.validate_phone_number(
        phone_number=phone_number,
    )

    otp_check = otp_services.verify_otp(
        to=number,
        code=otp,
        mock=is_mock(),
    )

    if not otp_check == 'approved':
        return None

    info = {
        'sub': phone_number
    }

    return info


def api_key_auth(apikey, required_scopes=None):
    # print(apikey, flush=True)
    # print(required_scopes, flush=True)
    user = mongoapi2.validate_api_key(apikey)

    if user and validate_scope({'sub': user}):
        # Prepare response
        info = {
            'sub': user
        }
        logger.debug(f'successful api_key_auth')
        return info

    return None


def registration(body):
    '''SGym Signup Endpoint'''
    # logger.debug(body)
    user_data = validate_user(body, 0)
    # logger.debug(user_data)
    if user_data['ok']:
        # logger.debug(f"User Details {user_data['data']}")
        result = mongoapi2.register(user_data)
        if result:
            response = {
                'ok': True,
                'message': 'User created successfully!',
                'username': result['username'],
                'user_id': result['user_id'],
                'user_phone_no': result['user_phone_no'],
            }
            return response, 201
        else:
            # General error message prevent people from guessing the username.
            return jsonify({
                'ok': False,
                'message': 'Unable to register, Please try again!',
            }), 401
    else:
        return jsonify({
            'ok': False,
            'message': f"Bad request parameters: {user_data['message']}",
        }), 400


def registrationWithActiveSgQR(body):
    '''SGym Signup Endpoint'''
    # logger.debug(body)
    user_data = validate_user(body, 1)
    # logger.debug(user_data)
    if user_data['ok']:
        # logger.debug(f"User Details {user_data['data']}")
        result = mongoapi2.registerWithActiveSgQR(user_data)
        if result:
            response = {
                'ok': True,
                'message': 'User created successfully!',
                'activeSgId': result['activeSgId'],
                'user_id': result['user_id']
            }
            return response, 201
        else:
            # General error message prevent people from guessing the username.
            return jsonify({
                'ok': False,
                'message': 'Unable to register, Please try again!'
            }), 401
    else:
        return jsonify({
            'ok': False,
            'message': f"Bad request parameters: {user_data['message']}",
        }), 400


def login(user):
    logger.debug(f'login')

    if not user:
        return jsonify({
            'ok': False,
            'message': 'Invalid username and password combination'
        }), 401

    # Generate JWT
    # access_token = generate_access_token(user['user_id'])
    # refresh_token = generate_refresh_token(user['user_id'])
    access_token, refresh_token = refresh_tokens(user)

    # Prepare response
    token = {
        'ok': True,
        'sessionKey': access_token,
        'refreshKey': refresh_token,
        'user_id': user,
    }
    return token, 200


def loginWithActiveSgId(user, body):
    logger.debug(f'login')
    logger.debug("user123  testing below")
    # logger.debug( "user123" + body['timestamp'])
    # y = json.loads(response.text)
    mobileDate = datetime.fromisoformat(body['timestamp'][:-1])
    serverDate = datetime.now() + timedelta(minutes=6)
    logger.debug(mobileDate)
    logger.debug(serverDate)
    logger.debug((serverDate - mobileDate))
    logger.debug((serverDate - mobileDate).total_seconds())
    logger.debug("user123 testing over")

    if ((serverDate - mobileDate).total_seconds() > 7260):
        return jsonify({
            'ok': False,
            'message': 'Invalid QR Code'
        }), 401

    # Generate JWT
    # access_token = generate_access_token(user['user_id'])
    # refresh_token = generate_refresh_token(user['user_id'])
    access_token, refresh_token = refresh_tokens(user)

    # Prepare response
    token = {
        'ok': True,
        'sessionKey': access_token,
        'refreshKey': refresh_token,
        'user_id': user,
    }
    return token, 200


def requestOtp(body):
    '''Routes from /requestOtp

    Args:
        user (str): Not used
        body (dict): Request body
    Returns:
        JSON object containing [anti_csrf] token
    '''
    logger.debug(f'requestOtp')

    # Check headers
    if not has_web_headers():
        return {}, 400

    # Check phone number is registered in database
    phone_number = body['phone_number']
    number = mongoapi2.validate_phone_number(
        phone_number=phone_number,
    )

    if not number:
        return {}, 400

    # Find user id
    user_id = mongoapi2.find_user_by_phone_number(
        phone_number=number,
    )

    if not user_id:
        return {}, 404

    # Send SMS OTP
    otp_services.sms_otp(
        to=number,
        mock=is_mock(),
    )

    return {}, 202


def loginWithOtp(user, body):
    '''Routes from /loginWithOtp

    Args:
        user (str): Not used
        body (dict): Request body
    Returns:
        JSON object containing [anti_csrf] token
    '''
    logger.debug(f'loginWithOtp')

    phone_number = body['phone_number']
    if user != phone_number:
        return {}, 400

    # Check headers
    if not has_web_headers():
        return {}, 400

    # Find user id
    user_id = mongoapi2.find_user_by_phone_number(
        phone_number=phone_number,
    )

    if not user_id:
        return {}, 404

    # Generate JWT
    access_token, refresh_token = refresh_tokens(user_id)

    # Prepare response
    anti_csrf, _ = generate_anti_csrf_token(
        user_id=user_id,
        anti_csrf=access_token.split('.')[-1],
    )
    token = {
        'ok': True,
        'anti_csrf': anti_csrf,
        'user_id': user_id,
    }
    res = make_response(token, 200)
    res.set_cookie(
        key="sessionKey",
        value=access_token,
        httponly=True,
        samesite='None',
        secure=True,
    )
    res.set_cookie(
        key="refreshKey",
        value=refresh_token,
        httponly=True,
        samesite='None',
        secure=True,
    )
    return res


def logout(user):
    logger.debug(f'logout')

    result = mongoapi2.logout(user)

    if result:
        result = {}
        status_code = 202
    else:
        result = {}
        status_code = 400

    return result, status_code


def create_service_account(user, body):
    res = mongoapi2.create_service_account(body)
    # print(res, flush=True)

    # Make status
    if res:
        status_code = 201
    else:
        status_code = 400

    return res, status_code


def delete_service_account(user, accountName):
    result = mongoapi2.delete_service_account(accountName)
    # print(res, flush=True)

    keys = result.keys()
    # Make status
    if 'error' in keys:
        if 'Bad' in result['error']:
            status_code = 400
        if 'not found' in result['error']:
            status_code = 404
    else:
        status_code = 201

    return result, status_code


def refresh(user):
    logger.debug(f'refresh')

    # Generate JWT
    access_token, refresh_token = refresh_tokens(user)

    # Prepare response
    token = {
        'ok': True,
        'sessionKey': access_token,
        'refreshKey': refresh_token,
        'user_id': user,
    }

    return token, 200


def round_up_16(x: int) -> int:
    # Bitwise trick to round up to next multiple
    # https://www.geeksforgeeks.org/round-to-next-greater-multiple-of-8/
    return (x + 15) & (-16)


def generate_activesg_id_token(activesg_id: str, token: str) -> str:
    # Payload in dict
    payload = {
        ID_KEY: activesg_id,
        'token': token,
    }

    # Convert to JSON string
    payload_str = json.dumps(payload)

    # Pad to multiples of 16 plus 8 for salt
    width = round_up_16(len(payload_str)) + 8
    payload_padded = payload_str.zfill(width)

    # Encrypt
    payload_encrypted = encrypt(payload_padded)

    # Convert to base64
    payload_encoded = b64encode(payload_encrypted).decode()

    return payload_encoded


def validate_activesg_id(activesg_id: str) -> bool:
    pattern = '^[0-9]+$'  # At least 1 number
    pattern_check = re.match(pattern, activesg_id)

    if not pattern_check:
        return False

    return True


def post_activesgids(body):
    '''Routes from POST /activesgids

    Args:
        body (dict): Request body
    Returns:
        JSON object containing ActiveSG ID token
    '''
    # Guard missing key
    if ID_KEY not in body.keys():
        response = {
            'ok': False,
            'error': 'Bad request body',
        }
        return response, 400

    # Guard malformed value
    activesg_id = body[ID_KEY]
    if not validate_activesg_id(activesg_id):
        response = {
            'ok': False,
            'error': 'Bad request body',
        }
        return response, 400

    # Generate random uuid
    token = uuid.uuid4().hex

    # Generate payload
    payload = generate_activesg_id_token(activesg_id, token)

    # Set key in redis, time to live = 60 seconds
    name = f'activesgids:{activesg_id}'
    with RDB() as r:
        r.set(
            name=name,
            value=token,
        )
        r.expire(
            name=name,
            time=60,  # seconds
        )

    # Create response
    response = {
        'activesg_id_token': payload
    }

    return response, 201


def wearable_login(body):
    '''Routes from POST /wearable/hpbWatch/login

    Args:
        body (dict): Request body
    Returns:
        JSON object containing ActiveSG ID token
    '''
    if 'peripheral_id' not in body.keys():
        response = {
            'ok': False,
            'error': 'Bad request body',
        }
        return response, 400

    activesg_id = mongoapi2.get_user_id_using_wearable(body['peripheral_id'])

    response = {
        'activesg_id': activesg_id
    }

    return response, 201


def post_activesgids_login(user, body):
    '''Routes from POST /activesgids/login

    Args:
        user (str): User id from authentication
        body (dict): Request body
    Returns:
        JSON object containing JWT token
    '''
    # Check input timestamp
    mobile_date = datetime.fromisoformat(body['timestamp'][:-1])
    server_date = datetime.now() + timedelta(minutes=6)

    if ((server_date - mobile_date).total_seconds() > 7260):
        return jsonify({
            'ok': False,
            'message': 'Invalid QR Code'
        }), 401

    # Generate JWT
    access_token, refresh_token = refresh_tokens(user)

    # Prepare response
    token = {
        'ok': True,
        'sessionKey': access_token,
        'refreshKey': refresh_token,
        'user_id': user,
    }

    return token, 200
