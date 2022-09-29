
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
        'systolic',
        'diastolic',
        'arterial',
        'pulse',
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

    out['available'] = bool(int(out['available']))
    out['name'] = out['name']
    out['type'] = out['type']

    if out['user'] is not None:
        out['user'] = out['user']

    if out['uuid'] is not None:
        out['uuid'] = out['uuid']

    if out['systolic'] is not None:
        out['systolic'] = float(out['systolic'])

    if out['diastolic'] is not None:
        out['diastolic'] = float(out['diastolic'])

    if out['arterial'] is not None:
        out['arterial'] = float(out['arterial'])

    if out['pulse'] is not None:
        out['pulse'] = float(out['pulse'])


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
    if key == 'diastolic':
        k = f'{machineId}:diastolic'
        v = float(value)
    if key == 'systolic':
        k = f'{machineId}:systolic'
        v = float(value)
    if key == 'available':
        k = f'{machineId}:available'
        v = int(bool(int(value)))
    if key == 'user':
        k = f'{machineId}:user'
        v = value
    if key == 'arterial':
        k = f'{machineId}:arterial'
        v = float(value)
    if key == 'pulse':
        k = f'{machineId}:pulse'
        v = float(value)
    # if key == 'timestamp':
    #     k = f'{machineId}:timestamp'
    #     v = float(value)
    

   
    r.set(k, v)

    return True

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