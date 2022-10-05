import redis
import time
import config
import logging
# import graypy
import loggerwrapper


queue_name = 'orchestrator_queue'


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
logger = loggerwrapper.LoggerWrapper('Orchestrator wrapper').getLogger()
logger.info('Orchestrator wrapper logger ready')


def connectRedis(ip, port):
    """Connects to redis server and returns a redis client

    Args:
        ip: Redis server IP address
        port: Redis server port number

    Returns:
        Redis client
    """
    connected = False

    while(not connected):
        try:
            time.sleep(1)
            r = redis.Redis(ip, port)
            connected = r.ping()
        except Exception as e:
            logger.error(e)

    logger.info(f'Connected to {ip}:{port}!')

    return r


def acquireMachineId(ip, port, hostname, machine_type):
    '''Acquire a machine id from orchestrator.

    Args:
        ip: IP address of orchestrator
        port: Port of orchestrator
        hostname: Name of host requesting machine Id
        machine_type: Type of machine Id requested
    Return
        str: Machine Id.
    '''

    r_local = connectRedis(ip, port)
    payload = f'{hostname}:{machine_type}'
    r_local.lpush(queue_name, payload)
    logger.info('Pushed request to orchestrator, waiting for reply')
    key, value = r_local.brpop(hostname)
    machineID = value.decode()

    # Make MACHINEID and MACHINETYPE available as file
    with open('MACHINEID', 'x') as f:
        f.write(f'{machineID}\n')
    with open('MACHINETYPE', 'x') as f:
        f.write(f'{machine_type}\n')
    logger.info('Saved MACHINEID and MACHINETYPE as file')

    return machineID
