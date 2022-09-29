from routes.bpm.redisfunction2 import *
from routes.machines import xadd
from src import mongoapi2

import logging
import time
import json

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

def initialize_bpm_with_user(user: str, machineId: str, body: dict):
    """Routes /bpm/bpm/{machineId}/initializeBpmWithUser

       Args:
        user: Authenticated user
        machineId: Machine id
        body: Dict with a single key named [value]
      Returns:
        Nothing
    """

    result = mongoapi2.get_machines()

    for machine in result:
        machineDetails = redis_get_keyvalues(machine['uuid'])
        if(machineDetails['user'] == user):
            logger.debug('got repeat the user')
            del_key(user, machine['uuid'], 'user')

    # logger.debug(f'Step into initialize_weighing_scale_with_user({user}, {machineId}, {body})')

    # Routing
    r1 = del_key(user, machineId, 'user')
    r2 = set_key(user, machineId, 'user', body)
    r3 = set_key(user, machineId, 'systolic', {"value": 0.0})
    r4 = set_key(user, machineId, 'diastolic', {"value": 0.0})
    r5 = set_key(user, machineId, 'arterial', {"value": 0.0})
    r6 = set_key(user, machineId, 'pulse', {"value": 0.0})
    r7 = del_key(user, machineId, 'data_stream')


    logger.debug(r1[1] == 201)
    logger.debug(r2[1] == 201)
    logger.debug(r3[1] == 201)
    logger.debug(r4[1] == 201)
    logger.debug(r5[1] == 201)
    logger.debug(r6[1] == 201)
    logger.debug(r7[1] == 201)

    if ((r1[1] == 201) & (r2[1] == 201) & (r3[1] == 201) & (r4[1] == 201) & (r5[1] == 201) & (r6[1] == 201)
            & (r7[1] == 201)):

        result = {}
        status_code = 201
    else:
        result = {}
        status_code = 400

    return result, status_code

def get_keyvalues(user: str, machineId: str):
    """Routes /bpm/{machineId}/keyvalues

 
    Args:
      user: Authenticated user
      machineId: Machine id
    Returns:
      Dict containing key-value pairs
    """

    # logger.debug(f'Step into get_keyvalues({user}, {machineId})')

    # Routing
    result = redis_get_keyvalues(machineId)

    # Make status
    status_code = 200

    return result, status_code

def getBpMetricsList(userId, limit, location='', start_date=0, end_date=0):
    '''using get function in exercises to get result'''

    # get bp metrics list where exercise_name == "bpm"
    result = mongoapi2.mongoGetBpMetricsList(userId, "Blood Pressure Monitor", sort_date_by='DESC', limit=limit, location=location, start_date=start_date, end_date=end_date)

    # logger.debug(result)
    if 'error' in result.keys():
        if 'Bad' in result['error']:
            status_code = 400
        elif 'Not found' in result['error']:
            status_code = 404
    else:
        status_code = 200
        result = result['res']

    return result, status_code

def bpmUpdateRedis(user: str, machineId: str, body: dict):
    """Routes /bpm/{machineId}/bpmUpdateRedis:

       Args:
        user: Authenticated user
        machineId: Machine id
        body: Dict with a single key named [value]
      Returns:
        Nothing
    """
    # uses machine to set key and stuff
    # logger.debug(f'bpm update redis({user}, {machineId}, {body})')

    # Routing

    try:
        r1 = set_key(user, machineId, 'systolic',
                     {"value": body['systolic']})
        r2 = set_key(user, machineId, 'diastolic',
                     {"value": body['diastolic']})
        r3 = set_key(user, machineId, 'arterial',
                     {"value": body['arterial']})
        r4 = set_key(user, machineId, 'pulse',
                     {"value": body['pulse']})
        # r5 = set_key(user, machineId, 'timestamp',
        #              {"value": body['timestamp']}),

        if isinstance(body, dict):
            r5 = xadd(user, machineId, 'data_stream', body)


        logger.debug(r1[1] == 201)
        logger.debug(r2[1] == 201)
        logger.debug(r3[1] == 201)
        logger.debug(r4[1] == 201)
        # logger.debug(r5[1] == 201)

    except Exception as e:
        logger.error(f'bpmUpdateRedis, {e}, {body}')

    logger.debug("Bpm update redis" + str(r1[1]) + " " + str(r2[1]) + " " + str(r3[1]) + " " + str(r4[1]) + " ")
    # Make status
    if ((r1[1] == 201) & (r2[1] == 201) & (r3[1] == 201) & (r4[1] == 201)):
        result = {}
        status_code = 201
        mongoapi2.dispatch_bpm(machineId)

        #mongoapi2.dispatch_machine(user, machineId)

    else:
        result = {}
        status_code = 400

    return result, status_code

    pass

def set_key(user: str, machineId: str, key: str, body: dict):
    """Routes /machines/{machineId}/keyvalues/{key}

    Args:
      user: Authenticated user
      machineId: Machine id
      key: Name of key
      body: Dict with a single key named [value]
    Returns:
      Nothing
    """

    # logger.debug(f'Step into set_key({user}, {machineId}, {key}, {body})')

    # Validate type
    error_msg = {'Error': 'Value type error'}
    error_code = 400
    value = body['value']
    logger.debug(f'{value} is type {type(value)}')
    if key == 'systolic' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'diastolic' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'arterial' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'pulse' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code

    # Routing
    result = redis_set_key(machineId, key, body)

    # Make status
    if result:
        result = {}
        status_code = 201
    else:
        result = {}
        status_code = 400

    return result, status_code

def del_key(user: str, machineId: str, key: str):
    """Routes /machines/{machineId}/keyvalues/{key}

    Args:
      user: Authenticated user
      machineId: Machine id
      key: Name of key
    Returns:
      Nothing
    """

    # logger.debug(f'Step into del_key({user}, {machineId}, {key})')

    # Validate type
    error_msg = {'Error': 'Value type error'}
    error_code = 400
    accepted_strings = {'data_stream', 'user'}

    if key not in accepted_strings:
        return error_msg, error_code

    # Routing
    result = redis_del_key(machineId, key)

    # Make status
    if result:
        result = {}
        status_code = 201
    else:
        result = {}
        status_code = 400

    return result, status_code
