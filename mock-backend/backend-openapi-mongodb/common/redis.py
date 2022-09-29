import time
import json
import redis


# ---------------------------------------------------------------------------- #
#                               Setting up redis                               #
# ---------------------------------------------------------------------------- #

redis_ip = "redis"
redis_port = 6379
r = redis.Redis(host=redis_ip, port=redis_port)


def setKey(machineId: str, key: str, body: dict):
    try:
        r.set(f"{machineId}:{key}", body["value"])
        return True
    except:
        return False


def incrementKey(machineId: str, key: str, body: dict):
    try:
        value = float(body["value"])
        r.incrbyfloat(f"{machineId}:{key}", value)
        return True
    except:
        return False


def decrementKey(machineId: str, key: str, body: dict):
    try:
        value = float(body["value"])
        r.incrbyfloat(f"{machineId}:{key}", -abs(value))
        return True
    except:
        return False

def getKey(machineId: str, key: str, dataTypeDict: dict):
    try:
        full_keys = ["{}:{}".format(machineId, ele) for ele in dataTypeDict.keys()]
        values = r.mget(full_keys)
        # Make return value
        output = {}
        for k, v in zip(keys, values):
            if v:
                output[k] = v.decode()

            else:
                output[k] = v
        
        return output
    except:
        return False

def xadd(machineId: str, key: str, body: dict):
    """Adds an item to redis stream at [key]

    Args:
      machineId: Machine id
      key: Redis stream key
      body: Dict to add
    Returns:
      True is success, False otherwise
    """
    try:
        logger.debug(f"xadd()")
        k = f"{machineId}:{key}"
        v = body
        r.xadd(k, v)
        return True
    except:
        return False

