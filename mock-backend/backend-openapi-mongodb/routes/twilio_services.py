import os
import logging

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


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


def get_secrets():
    secrets = {
        "account_sid": os.environ['TWILIO_ACCOUNT_SID'],
        "auth_token": os.environ['TWILIO_AUTH_TOKEN'],
        "service_sid": os.environ['TWILIO_SERVICE_SID'],
    }

    return secrets


def sms_otp(to: str, mock: bool = False) -> str:
    '''Request SMS OTP

    Args:
        to (str): Phone number
        mock (bool): For testing. If True, returns 'pending'

    Returns:
        str
    '''
    if mock:
        logger.info(f'sms_otp mock is {mock}')
        return 'pending'

    secrets = get_secrets()
    account_sid = secrets["account_sid"]
    auth_token = secrets["auth_token"]
    service_sid = secrets["service_sid"]

    client = Client(account_sid, auth_token)

    verification = client \
        .verify \
        .services(service_sid) \
        .verifications.create(
            to=to,
            channel='sms'
        )

    return verification.status


def verify_otp(to: str, code: str, mock: bool = False) -> str:
    '''Verify SMS OTP

    Args:
        to (str): Phone number
        code (str): OTP
        mock (bool): For testing. If True, returns 'approved'

    Returns:
        str
    '''
    if mock:
        logger.info(f'verify_otp mock is {mock}')
        return 'approved'

    secrets = get_secrets()
    account_sid = secrets["account_sid"]
    auth_token = secrets["auth_token"]
    service_sid = secrets["service_sid"]

    client = Client(account_sid, auth_token)

    try:
        verification_check = client \
            .verify \
            .services(service_sid) \
            .verification_checks.create(
                to=to,
                code=code,
            )

        return verification_check.status
    except TwilioRestException:
        return 'TwilioRestException'
