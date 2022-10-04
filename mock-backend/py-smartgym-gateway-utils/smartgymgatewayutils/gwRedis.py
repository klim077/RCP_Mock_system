import time

import redis

from . import logger


def connect(ip, port, timeout=1):
    """Connects to redis server and returns a redis client

    Args:
        ip (str): Redis server IP address
        port (int): Redis server port number
        timeout (int): Connection timeout

    Returns:
        Redis client
    """
    logger.info(f'Connecting to redis at {ip}:{port}')

    connected = False
    attempts = 0
    while(not connected):
        attempts += 1
        logger.info(f'Connecting to redis attempt {attempts}...')
        try:
            time.sleep(timeout)
            r = redis.Redis(ip, port)
            connected = r.ping()
        except Exception as e:
            logger.error(e)

    logger.info('Connected to redis!')

    return r
