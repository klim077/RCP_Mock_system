
import requests
import datetime
import pytz
from common import logger
from common.config import *
from common.config import redis_ip, redis_port
import redis

tz_sg = pytz.timezone('Singapore')

r = redis.Redis(host=redis_ip, port=redis_port)

rower_dict ={
    "distance":float,
    "cadence":float,
    "calories":float,
    "strokes":float,
    "timestamp":datetime.time,
    "workoutTime":float,
    "pace":float,
    "power":float,
    "rowingTime": float,
    "heartRate": float,
    "interval": float,
    "rec":bool,
}

# def get_secret(secret_name):
#     try:
#         with open(f'/run/secrets/{secret_name}', 'r') as secret_file:
#             return secret_file.read().splitlines()[0]
#     except IOError:
#         raise

# headers = {
#     'X-API-Key': get_secret('APIKey'),
# }


# Helpers
def rget(key):
    value = r.get(key)
    # logger.debug(f'Get: {key}, Value: {value}')

    if value:
        return value.decode()
    else:
        return value

def j(*args):
    return ':'.join([str(ele) for ele in args])

def getRedisChannelAsDict(key):

    #Returns a dictionary of the current values stored in a particular key
    dicto = {}
    keyPattern = key + ":*"
    for key in r.scan_iter(keyPattern):
        ky = key.decode().split(":")[1]
        if ky != "data_stream":
            dicto[ky] = r.get(key).decode()
    if "timestamp" in dicto:
        timeFloat = float(dicto['timestamp'])
        dicto['timestamp'] = datetime.datetime.fromtimestamp(timeFloat, tz=tz_sg)
        print(f'dicto: {dicto}')

    # return processRedisChannel(dicto)
    return dicto

def getKey(machineId: str, dataTypeDict: dict):
    output = {}

    try:
        machineId = machineId.strip()
        full_keys = ["{}:{}".format(machineId, ele) for ele in dataTypeDict.keys()]
        logger.info(full_keys)
        values = r.mget(full_keys)
        # Make return value
        output = {}
        for k, v in zip(dataTypeDict.keys(), values):
            if v:
                output[k] = v.decode()

            else:
                output[k] = v

        return output
    except:
        return output

def processRedisChannel(redisChannel):

    # do something
    print(f'redisChannel: {redisChannel}')

    return redisChannel

# string to bool
def getBool(rec):

    if (rec == "True"):
        return True
    elif (rec == "False"):
        return False
    else:
        logger.debug("rec undefined")
        return None

def rowerUpdateRedisFromPostman(machineId, rower_dict):

    url = 'http://{ip}:{port}/{ver}/machines/{machineId}/rowerUpdateRedisFromPostman'.format(
        ip=mongoapi_ip,
        port=mongoapi_port,
        ver=mongoapi_version,
        machineId=machineId
    )

    logger.info(f'posting to URL: {url}')
    print(f'posting to URL: {url}')
    logger.info(f'rower_dict: {rower_dict}')
    print(f'rower_dict: {rower_dict}')

    response = requests.post(
        url=url,
        # headers=headers,
        json=rower_dict
    )

    if response.ok:
        logger.info('post status_code: {}'.format(response.status_code))
    else:
        logger.error('post status_code: {}, {}'.format(
            response.status_code, response.text))    

    return response