
import time
import json
import redis


# ---------------------------------------------------------------------------- #
#                               Setting up redis                               #
# ---------------------------------------------------------------------------- #

redis_ip = 'redis'
redis_port = 6379
r = redis.Redis(host=redis_ip, port=redis_port)

def redis_get_keyvalues(machineId: str):
    """Get selected keys for a weighing scale machine from redis
    Args:
      machineId: Machine id
    Returns:
      Dict of selected keys with values
    """

    # Selected keys
    keys = [
        'user',
        'name',
        'type',
        'uuid',
        'location',
        'available',
        'bmi',
        'waterPercentage',
        'protein',
        'musclePercentage',
        'basalMetalbolism',
        'boneMass',
        'bodyFatPercentage',
        'height',
        'weight',
        'isStable',
        'unit',
        'hasImpedance',
        'impedance',
        'isConnected',
        'hasLoad',
        'LBMCoefficient',
        'BMR',
        'visceralFat',
        'idealWeight',
        'fatMassToIdeal',
        'bodyType',
        'metabolicAge'
    ]

    # Pad with machineId
    full_keys = ['{}:{}'.format(machineId, ele) for ele in keys]

    # Get multiple keys
    values = r.mget(full_keys)

    # Make return value
    out = {}
    for k, v in zip(keys, values):
        if v:
            out[k] = v.decode()
        else:
            out[k] = v

    out['name'] = out['name']
    out['isConnected'] = out['isConnected']
    out['impedance'] = out['impedance']
    out['isStable'] = out['isStable']
    out['unit'] = out['unit']
    out['hasImpedance'] = out['hasImpedance']
    out['hasLoad'] = out['hasLoad']
    out['location'] = out['location']
    out['type'] = out['type']

    if out['available'] is not None:
        out['available'] = bool(int(out['available']))

    if out['user'] is not None:
        out['user'] = out['user']

    if out['uuid'] is not None:
        out['uuid'] = out['uuid']

    if out['weight'] is not None:
        out['weight'] = float(out['weight'])

    if out['height'] is not None:
        out['height'] = float(out['height'])

    if out['protein'] is not None:
        out['protein'] = float(out['protein'])

    if out['musclePercentage'] is not None:
        out['musclePercentage'] = float(out['musclePercentage'])

    if out['basalMetalbolism'] is not None:
        out['basalMetalbolism'] = float(out['basalMetalbolism'])

    if out['boneMass'] is not None:
        out['boneMass'] = float(out['boneMass'])

    if out['bodyFatPercentage'] is not None:
        out['bodyFatPercentage'] = float(out['bodyFatPercentage'])

    if out['waterPercentage'] is not None:
        out['waterPercentage'] = float(out['waterPercentage'])

    if out['bmi'] is not None:
        out['bmi'] = float(out['bmi'])

    if out['metabolicAge'] is not None:
        out['metabolicAge'] = float(out['metabolicAge'])

    if out['LBMCoefficient'] is not None:
        out['LBMCoefficient'] = float(out['LBMCoefficient'])

    if out['BMR'] is not None:
        out['BMR'] = float(out['BMR'])

    if out['visceralFat'] is not None:
        out['visceralFat'] = float(out['visceralFat'])

    if out['idealWeight'] is not None:
        out['idealWeight'] = float(out['idealWeight'])

    if out['fatMassToIdeal'] is not None:
        out['fatMassToIdeal'] = float(out['fatMassToIdeal'])

    if out['bodyType'] is not None:
        out['bodyType'] = float(out['bodyType'])

    return out


def redis_set_key(machineId: str, key: str, body: dict):
    """Set key for a machine in redis

    Args:
      machineId: Machine id
      key: Key to set
      body: Dict containing value to set
    Returns:
      True is success, False otherwise
    """

    value = body['value']

    k, v = '', ''
    if key == 'height':
        k = f'{machineId}:height'
        v = float(value)
    if key == 'weight':
        k = f'{machineId}:weight'
        v = float(value)
    if key == 'available':
        k = f'{machineId}:available'
        v = int(bool(int(value)))
    if key == 'user':
        k = f'{machineId}:user'
        v = value
    if key == 'bmi':
        k = f'{machineId}:bmi'
        v = float(value)
    if key == 'waterPercentage':
        k = f'{machineId}:waterPercentage'
        v = float(value)
    if key == 'bodyFatPercentage':
        k = f'{machineId}:bodyFatPercentage'
        v = float(value)
    if key == 'boneMass':
        k = f'{machineId}:boneMass'
        v = float(value)
    if key == 'basalMetalbolism':
        k = f'{machineId}:basalMetalbolism'
        v = float(value)
    if key == 'musclePercentage':
        k = f'{machineId}:musclePercentage'
        v = float(value)
    if key == 'protein':
        k = f'{machineId}:protein'
        v = float(value)
    if key == 'isStable':
        k = f'{machineId}:isStable'
        v = str(value)
    if key == 'unit':
        k = f'{machineId}:unit'
        v = str(value)
    if key == 'hasImpedance':
        k = f'{machineId}:hasImpedance'
        v = str(value)
    if key == 'impedance':
        k = f'{machineId}:impedance'
        v = float(value)
    if key == 'isConnected':
        k = f'{machineId}:isConnected'
        v = str(value)
    if key == 'hasLoad':
        k = f'{machineId}:hasLoad'
        v = str(value)
    if key == 'LBMCoefficient':
        k = f'{machineId}:LBMCoefficient'
        v = float(value)
    if key == 'BMR':
        k = f'{machineId}:BMR'
        v = float(value)
    if key == 'visceralFat':
        k = f'{machineId}:visceralFat'
        v = float(value)
    if key == 'idealWeight':
        k = f'{machineId}:idealWeight'
        v = float(value)
    if key == 'fatMassToIdeal':
        k = f'{machineId}:fatMassToIdeal'
        v = float(value)
    if key == 'bodyType':
        k = f'{machineId}:bodyType'
        v = float(value)
    if key == 'metabolicAge':
        k = f'{machineId}:metabolicAge'
        v = float(value)
    if key == 'timestamp':
        k = f'{machineId}:timestamp'
        v = float(value)
    try:
        r.set(k, v)
        return True
    except:
        return False

def redis_del_key(machineId: str, key: str):
    """Delete key for a machine in redis

    Args:
      machineId: Machine id
      key: Key to delete
    Returns:
      True is success, False otherwise
    """

   

    k = ''
    if key == 'user':
        k = f'{machineId}:user'
    if key == 'data_stream':
        k = f'{machineId}:data_stream'

    
    r.delete(k)

    return True