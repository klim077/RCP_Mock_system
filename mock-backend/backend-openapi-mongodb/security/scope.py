from bson.objectid import ObjectId
import re
from connexion import request
from src import mongoapi2

import logging

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
# logger.setLevel(logging.WARNING)
# logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.ERROR)
ch = logging.StreamHandler()
format_str = '%(levelname)s:%(lineno)s:%(message)s'
formatter = logging.Formatter(format_str)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info('Logger ready')

# Regex pattern to match service accounts
svc_pattern = '^sgymsvcs\$.+'
admin_pattern = 'sgym$admin'
refresh_pattern = 'refresh_token'

user_pattern = '/users/([\dabcdef]{24})/?'

serviceaccount_pattern = '/serviceaccounts$'

refresh_token_pattern = '/tokens/refresh$'


def validate_scope(claim):
    """ Validates a user can access path in request.

    Args:
        claim: Valid JWT claim
    Returns:
        True or None
    """

    logger.debug(f'validate_scope()')
    
    user = claim['sub']
    path = request.path
    # logger.info(f'validate_scope {user} on {path}')

    # Check if token is in database
    if claim.get(refresh_pattern):  # if refresh token
        if not mongoapi2.is_refresh_token_good(claim):
            logger.info('Access token not found in database')
            return None
    elif claim.get('iat'):  # if jwt token
        if not mongoapi2.is_access_token_good(claim):
            logger.info('Refresh token not found in database')
            return None
    else:  # if apikey
        pass

    # /users
    userId = re.search(user_pattern, path, re.IGNORECASE)
    # logger.debug(f'userId: {userId}')
    if userId:
        # using jwt token
        if userId.group(1) == user:
            return True
        # using apikey
        elif re.match(svc_pattern, user):
            return True
        else:
            return None

    # /serviceaccounts
    serviceaccount = re.search(serviceaccount_pattern, path, re.IGNORECASE)
    logger.debug(f'serviceaccount')
    if serviceaccount:
        # accept only specific user using apikey
        if user == admin_pattern:
            return True
        else:
            return None

    # /tokens/refresh
    refreshtoken = re.search(refresh_token_pattern, path, re.IGNORECASE)
    logger.debug(f'refreshtoken')
    if refreshtoken:
        logger.debug(f'refreshtoken group(0)')
        # accept only refresh token scope
        if claim[refresh_pattern]:
            logger.debug(claim)
            return True
        else:
            return None

    # other endpoints using apikey
    if re.match(svc_pattern, user):
        logger.debug(f'other endpoints using apikey ')
        return True

    # other endpoints using jwt
    try:
        objId = ObjectId(user)
        logger.debug(f'other endpoints using jwt')
        return True
    except:
        return None

    logger.info('default return None')
    return None
