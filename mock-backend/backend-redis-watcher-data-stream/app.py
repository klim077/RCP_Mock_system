import time
import logging
import json

import redis
from redis.client import PubSub

# Set up logger
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

logger = logging.getLogger(__name__)
# logger.setLevel(logging.ERROR)
# logger.setLevel(logging.WARNING)
# logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
format_str = '%(levelname)s:%(lineno)s:%(message)s'
formatter = logging.Formatter(format_str)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info('Logger ready')


# Define variables
redis_ip = 'redis'
redis_port = 6379

'''Redis Keyspace value
K  Keyspace events, published with __keyspace@<db>__ prefix.
E  Keyevent events, published with __keyevent@<db>__ prefix.
g  Generic commands (non-type specific) like DEL, EXPIRE, RENAME, ...
$  String commands
l  List commands
s  Set commands
h  Hash commands
z  Sorted set commands
t  Stream commands
x  Expired events (events generated every time a key expires)
e  Evicted events (events generated when a key is evicted for maxmemory)
m  Key miss events (events generated when a key that doesn't exist is accessed)
A  Alias for "g$lshztxe", so that the "AKE" string means all events except "m".
'''
# Keyspace events, String, Generic, and Stream commands only
redis_keyspace_value = 'K$gt'
redis_keyspace_subscribe_pattern = '__key*__:*:data_stream'

redis_connect_timeout = 1


def redis_machine_message(machine: str) -> str:
    '''Returns formatted message containing machine id.

    Args:
        machine (str): Machine id
    Returns:
        str
    '''
    out = json.dumps({'machine_id': machine})
    return out


def redis_user_template(machine: str) -> str:
    '''Returns full redis key of user in machine.

    Args:
        machine (str): Machine id
    Returns:
        str
    '''
    key = f'{machine}:user'
    return key


def connect_redis(host: str, port: int) -> redis.Redis:
    '''Connects to redis server.

    Args:
        host (str): Hostname or IP
        port (int): Port number
    Returns:
        redis.Redis object
    '''
    connected = False
    r = None

    while(not connected):
        try:
            time.sleep(redis_connect_timeout)  # in secs
            logger.info(f"Connecting to {host}:{port}!")
            r = redis.Redis(
                host=host,
                port=port,
                decode_responses=True,
            )
            connected = r.ping()
        except Exception as e:
            logger.error(e)

    logger.info(f'Connected to {host}:{port}!')

    return r


def configure_redis_keyspace(client: redis.Redis, value: str):
    '''Use config set to configure redis keyspace notification.

    Args:
        client (Redis): Redis client
        value (str): Keyspace notification parameters
    Returns:
        Nothing
    '''

    logger.info(f'Configure Redis Keyspace Notification Events to {value}')
    client.config_set('notify-keyspace-events', value)


def redis_subscribe(client: redis.Redis, pattern: str) -> PubSub:
    '''Get a Redis PubSub object

    Args:
        client (Redis): Redis client
        pattern (str): Pattern to subscribe to
    Returns:
        PubSub object
    '''

    logger.info('Get pubsub object')

    # Create pubsub object
    p = client.pubsub()

    # Subscribe to pattern
    p.psubscribe(pattern)

    return p


def split_message(message: dict) -> dict:
    '''Split a keyspace notification message.
    Assumes the format a:b:c where:
        a: the keyspace prefix
        b: machine id
        c: key

    Args:
        message (dict): Keyspace notification message
    Returns:
        dict containing keys 'keyspace_prefix', 'machine_id', 'key'
    '''
    logger.info('Split message')
    # logger.debug(message)

    channel_key = 'channel'
    if channel_key in message:
        decoded = message[channel_key].split(':')
        # logger.debug(decoded)
        return {
            'keyspace_prefix': decoded[0],
            'machine_id': decoded[1],
            'key': decoded[2]
        }

    return {}


def check_has_user(client: redis.Redis, machine: dict) -> bool:
    '''Checks if user is set in machine

    Args:
        client (Redis): Redis client
        machine (str): Machine ID
    Returns:
        bool
    '''
    logger.info('Check is user is set in machine')
    # logger.debug(machine)

    key = redis_user_template(machine=machine)
    result = client.exists(key)

    if result == 0:
        return False
    else:
        return True


def publish_to_user(client: redis.Redis, machine: str):
    '''Publish machine id to the user channel defined under machine

    Args:
        client (Redis): Redis client
        machine (str): Machine ID
    Returns:
        Nothing
    '''
    logger.info('Publish to machine user')
    # logger.debug(machine)

    key = redis_user_template(machine=machine)
    logger.info(f'key: {key}')
    logger.info(f'channel: {client.get(key)}')

    client.publish(
        client.get(key),
        redis_machine_message(machine=machine),
    )


def main():
    logger.info("Start main loop")

    r = connect_redis(
        host=redis_ip,
        port=redis_port,
    )
    logger.info('Redis OK')

    configure_redis_keyspace(
        client=r,
        value=redis_keyspace_value,
    )

    p = redis_subscribe(
        client=r,
        pattern=redis_keyspace_subscribe_pattern,
    )

    logger.info('Start listening')
    for new_message in p.listen():
        logger.info('New message received')
        # logger.debug(new_message)

        # Decode message
        message = split_message(message=new_message)
        machine = message['machine_id']

        # Check if machine has user set
        has_user = check_has_user(
            client=r,
            machine=machine,
        )

        # Publish to user channel
        if has_user:
            publish_to_user(
                client=r,
                machine=machine,
            )


if __name__ == '__main__':
    logger.info("Main entry.")
    main()
    logger.info('All done.')
