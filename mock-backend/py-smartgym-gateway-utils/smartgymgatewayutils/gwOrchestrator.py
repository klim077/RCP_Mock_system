import time
import logging
import os

import redis
import graypy

from . import gwRedis
from . import logger


queue_name = 'orchestrator_queue'


def acquireMachineId(ip, port, hostname, machine_type):
    '''Acquire a machine id from orchestrator.

    Args:
        ip: IP address of orchestrator
        port: Port of orchestrator
        hostname: Name of host requesting machine Id
        machine_type: Type of machine Id requested

    Returns:
        str: Machine Id.
    '''

    # Connect to redis
    r_local = gwRedis.connect(ip, port)

    # Push request into redis list
    payload = f'{hostname}:{machine_type}'
    r_local.lpush(queue_name, payload)
    logger.info('Pushed request to orchestrator, waiting for reply')

    # Wait for reply in redis list named [hostname]
    key, value = r_local.brpop(hostname)
    machineID = value.decode()
    logger.info('Received reply from orchestrator')

    # Make MACHINEID and MACHINETYPE available as file
    with open('MACHINEID', 'x') as f:
        f.write(f'{machineID}\n')
    with open('MACHINETYPE', 'x') as f:
        f.write(f'{machine_type}\n')
    logger.info('Saved MACHINEID and MACHINETYPE as file')

    return machineID
