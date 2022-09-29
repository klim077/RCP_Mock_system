from routes.weighingScale.redisfunction import *
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


def initialize_weighing_scale_with_user(user: str, machineId: str, body: dict):
    """Routes /weighingScale/weighingscale/{machineId}/initializeWeighingScaleWithUser

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
    r3 = set_key(user, machineId, 'bmi', {"value": 0.0})
    r4 = set_key(user, machineId, 'Percentage', {"value": 0.0})
    r5 = set_key(user, machineId, 'musclePercentage', {"value": 0.0})
    r6 = set_key(user, machineId, 'waterPercentage', {"value": 0.0})
    r7 = set_key(user, machineId, 'protein', {"value": 0.0})
    r8 = set_key(user, machineId, 'basalMetalbolism', {"value": 0.0})
    r9 = set_key(user, machineId, 'boneMass', {"value": 0.0})
    r10 = set_key(user, machineId, 'weight', {"value": 0.0})
    r11 = set_key(user, machineId, 'height', {"value": 0.0})
    r12 = set_key(user, machineId, 'LBMCoefficient', {"value": 0.0})
    r13 = set_key(user, machineId, 'BMR', {"value": 0.0})
    r14 = set_key(user, machineId, 'visceralFat', {"value": 0.0})
    r15 = set_key(user, machineId, 'idealWeight', {"value": 0.0})
    r16 = set_key(user, machineId, 'fatMassToIdeal', {"value": 0.0})
    r17 = set_key(user, machineId, 'bodyType', {"value": 0.0})
    r18 = set_key(user, machineId, 'metabolicAge', {"value": 0.0})
    r19 = del_key(user, machineId, 'data_stream')


    logger.debug(r1[1] == 201)
    logger.debug(r2[1] == 201)
    logger.debug(r3[1] == 201)
    logger.debug(r4[1] == 201)
    logger.debug(r5[1] == 201)
    logger.debug(r6[1] == 201)
    logger.debug(r7[1] == 201)
    logger.debug(r9[1] == 201)
    logger.debug(r10[1] == 201)
    logger.debug(r11[1] == 201)
    logger.debug(r12[1] == 201)
    logger.debug(r13[1] == 201)
    logger.debug(r14[1] == 201)
    logger.debug(r15[1] == 201)
    logger.debug(r16[1] == 201)
    logger.debug(r17[1] == 201)
    logger.debug(r18[1] == 201)

    if ((r1[1] == 201) & (r2[1] == 201) & (r3[1] == 201) & (r4[1] == 201) & (r5[1] == 201) & (r6[1] == 201)
            & (r7[1] == 201) & (r8[1] == 201) & (r9[1] == 201) & (r9[1] == 201) & (r10[1] == 201) &
            (r11[1] == 201) & (r12[1] == 201) & (r13[1] == 201)
            & (r14[1] == 201) & (r15[1] == 201) & (r16[1] == 201) & (r17[1] == 201) & (r18[1] == 201) & (r19[1] == 201)):

        result = {}
        status_code = 201
    else:
        result = {}
        status_code = 400

    return result, status_code


def getBodyMetricsList(userId, limit, location='', start_date=0, end_date=0):
    '''using get function in exercises to get result'''

    result = mongoapi2.mongoGetBodyMetricsList(userId, sort_date_by='DESC', limit=limit, location=location, start_date=start_date, end_date=end_date)

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


def get_keyvalues(user: str, machineId: str):
    """Routes /weighing scale/{machineId}/keyvalues

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


def weighingScaleUpdateRedis(user: str, machineId: str, body: dict):
    """Routes /weighingScales/{machineId}/WeighingScaleUpdateRedis:

       Args:
        user: Authenticated user
        machineId: Machine id
        body: Dict with a single key named [value]
        call a postman to save weighing scale data
      Returns:
        Nothing
    """
    # uses machine to set key and stuff
    # logger.debug(f'weighing scale update redis({user}, {machineId}, {body})')

    # Routing

    try:
        r1 = set_key(user, machineId, 'isStable',
                     {"value": body['isStable']})
        r2 = set_key(user, machineId, 'weight',
                     {"value": body['weight']})
        r3 = set_key(user, machineId, 'unit',
                     {"value": body['unit']})
        r4 = set_key(user, machineId, 'hasImpedance',
                     {"value": body['hasImpedance']})
        r5 = set_key(user, machineId, 'impedance',
                     {"value": body['impedance']})
        r6 = set_key(user, machineId, 'isConnected',
                     {"value": body['isConnected']})
        r7 = set_key(user, machineId, 'timestamp',
                     {"value": body['timestamp']})
        r8 = set_key(user, machineId, 'hasLoad',
                     {"value": body['hasLoad']})

        logger.debug(r1[1] == True)
        logger.debug(r2[1] == True)
        logger.debug(r3[1] == True)
        logger.debug(r4[1] == True)
        logger.debug(r5[1] == True)
        logger.debug(r6[1] == True)
        logger.debug(r7[1] == True)
        logger.debug(r8[1] == True)
    except Exception as e:
        logger.error(f'weighingScaleUpdateRedis, {e}, {body}, 1:{r1}, 2:{r2}, 3:{r3}, 4:{r4}, 5:{r5}, 6:{r6}, 7:{r7}, 8:{r8}')

    # logger.debug("Weighing scale update redis" + str(r1[1]) + " " + str(r2[1]) + " " + str(r3[1]) + " " + str(r4[1]) + " "
    #              + str(r5[1]) + " " + str(r6[1]) + " " + str(r8[1]) + " ")
    # Make status
    if ((r1[1] == 201) & (r2[1] == 201) & (r3[1] == 201) & (r4[1] == 201) &
                (r5[1] == 201) & (r6[1] == 201) & (r8[1] == 201)
            ):
        result = {}
        status_code = 201
        mongoapi2.dispatch_weighingscale(machineId)
        #mongoapi2.dispatch_machine(user, machineId)
    else:
        result = {}
        status_code = 400

    return result, status_code


def weighingScaleUpdateRedisFromPostman(user: str, machineId: str, body: dict):
    """Routes /weighingscale/{machineId}/postWeighingScaleResultToRedis

       Args:
        user: Authenticated user
        machineId: Machine id
        body: Dict with a single key named [value]
        call a postman to save weighing scale data
      Returns:
        Nothing
    """
    # uses machine to set key and stuff

    # logger.debug(f'weighing scale update redis from postman({user}, {machineId}, {body})')

    # Routing

    try:

        r1 = set_key(user, machineId, 'bodyFatPercentage',
                     {"value": body['bodyFatPercentage']})
        r2 = set_key(user, machineId, 'bmi',
                     {"value": body['bmi']})
        r3 = set_key(user, machineId, 'boneMass',
                     {"value": body['boneMass']})
        r4 = set_key(user, machineId, 'basalMetalbolism',
                     {"value": body['basalMetalbolism']})
        r5 = set_key(user, machineId, 'protein', {"value": body['protein']})
        r6 = set_key(user, machineId, 'waterPercentage',
                     {"value": body['waterPercentage']})
        r7 = set_key(user, machineId, 'musclePercentage',
                     {"value": body['musclePercentage']})
        r8 = set_key(user, machineId, 'height',
                     {"value": body['height']})
        r9 = set_key(user, machineId, 'LBMCoefficient',
                     {"value": body['LBMCoefficient']})
        r10 = set_key(user, machineId, 'BMR', {"value": body['BMR']})
        r11 = set_key(user, machineId, 'visceralFat',
                      {"value": body['visceralFat']})
        r12 = set_key(user, machineId, 'idealWeight',
                      {"value": body['idealWeight']})
        r13 = set_key(user, machineId, 'fatMassToIdeal',
                      {"value": body['fatMassToIdeal']})
        r14 = set_key(user, machineId, 'bodyType', {"value": body['bodyType']})
        r15 = set_key(user, machineId, 'metabolicAge',
                      {"value": body['metabolicAge']})

        if isinstance(body, dict):
            r16 = xadd(user, machineId, 'data_stream', body)

        logger.debug(r1[1] == 201)
        logger.debug(r2[1] == 201)
        logger.debug(r3[1] == 201)
        logger.debug(r4[1] == 201)
        logger.debug(r5[1] == 201)
        logger.debug(r6[1] == 201)
        logger.debug(r7[1] == 201)
        logger.debug(r8[1] == 201)

        logger.debug(f'weighing scale r9()')

    except Exception as e:
        logger.error(f'weighingScaleUpdateRedisFromPostman, {e}')

    logger.debug("Weighing scale update redis" + str(r1[1]) + " " + str(r2[1]) + " " + str(r3[1]) + " " + str(r4[1]) + " "
                 + str(r5[1]) + " " + str(r6[1]) + " " + str(r7[1]) + " " + str(r8[1]) + " ")
    # Make status
    if ((r1[1] == 201) & (r2[1] == 201) & (r3[1] == 201) & (r4[1] == 201) &
                (r5[1] == 201) & (r6[1] == 201) & (
                r7[1] == 201) & (r8[1] == 201)
            ):
        result = {}
        status_code = 201

    else:
        result = {}
        status_code = 400

    return result, status_code


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
    if key == 'bodyFatPercentage' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'bmi' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'boneMass' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'basalMetalbolism' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'protein' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'waterPercentage' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'musclePercentage' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'isStable' and not isinstance(value, str):
        return error_msg, error_code
    if key == 'unit' and not isinstance(value, str):
        return error_msg, error_code
    if key == 'hasImpedance' and not isinstance(value, str):
        return error_msg, error_code
    if key == 'impedance' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'isConnected' and not isinstance(value, str):
        return error_msg, error_code
    if key == 'hasLoad' and not isinstance(value, str):
        return error_msg, error_code
    if key == 'weight' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'height' and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == 'timestamp' and not (isinstance(value, float)):
        return error_msg, error_code

    # Routing
    result = redis_set_key(machineId, key, body)
    # Make status
    if result == True:
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
