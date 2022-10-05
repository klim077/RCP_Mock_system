import os
import time
import logging
import csv
import socket
import json
import websocket
from typing import List

# from smartgymgatewayutils import config
# from smartgymgatewayutils import gwHTTP
# from smartgymgatewayutils import gwRedis
# from smartgymgatewayutils import gwConsul
# from smartgymgatewayutils import logger, loggerWrapper

import smartgymgatewayutils.config as config
import smartgymgatewayutils.gwHTTP as gwHTTP
import smartgymgatewayutils.gwRedis as gwRedis
# import smartgymgatewayutils.gwConsul as gwConsul
from smartgymgatewayutils.gwLogger import logger, loggerWrapper

# Get hostname
hostname = os.environ['HOSTNAME']

# Prepare logger
loggerName = f'submitter_{hostname}'
loggerWrapper.start(loggerName, level=logging.DEBUG)
logger.info(f'{loggerName} logger ready')

# Get environment variables
PROTOCOL = config.protocol
SERVER_IP = config.server_ip
SERVER_URL = config.server_url
GATEWAY_LOCATION = config.gateway_location
REDIS_IP = config.local_redis_ip
REDIS_PORT = config.local_redis_port
PHONEHOLDER_SERVICE_NAME = 'phoneholder_service'

# Local variables
submitter_topic = 'submitted'
WEBSOCKET_PROTOCOL = 'wss://' if PROTOCOL == 'https://' else 'ws://'
watcherUrl = f'{WEBSOCKET_PROTOCOL}{SERVER_IP}/watcher'


def initializeRedis2(r, data):
    logger.info(f'initializeRedis2 {r=} {data=}')

    # Clear all keys before starting
    r.delete(submitter_topic)

    for ele in data:
        # Push into list
        key = submitter_topic
        value = f"{ele['uuid']}:{ele['type']}"
        r.sadd(key, value)


def getMachinesDetails(hostname: str, port: int, location: str) -> List:
    '''Gets machine details using backend API.

    Args:
        hostname: str
        port: int
        location: str
    Returns:
        list: List of dict containing fields [uuid] and [type]
    '''

    logger.info(f'getMachinesDetails {hostname=} {port=} {location=}')

    url = f"http://{hostname}:{port}/{location}"

    logger.debug(f'{url=}')

    ret = gwHTTP.httpGet(url)

    logger.debug(f'{ret=}')

    return ret


def submit():
    logger.info(f'Submitting')

    # Loop to retry until success
    while True:
        # Get service details
        # PHONEHOLDER_SERVICE_IP = gwConsul.getAddress(
        #     name=PHONEHOLDER_SERVICE_NAME
        # )
        # PHONEHOLDER_SERVICE_PORT = gwConsul.getPort(name=PHONEHOLDER_SERVICE_NAME)
        PHONEHOLDER_SERVICE_IP = '192.168.1.119'
        PHONEHOLDER_SERVICE_PORT = 16000

        # Get details from backend
        details = getMachinesDetails(
            hostname=PHONEHOLDER_SERVICE_IP,
            port=PHONEHOLDER_SERVICE_PORT,
            location=GATEWAY_LOCATION,
        )

        # Break if details has been set
        if details != None:
            break

        # Else, log error message and retry
        msg = f'No machines details received'
        logger.error(msg)
        time.sleep(1)

    # Connect to local redis
    r = gwRedis.connect(
        REDIS_IP,
        REDIS_PORT
    )

    # Populate local redis with machine data
    initializeRedis2(r, details)
    r.close()

    logger.info('Submitted machine details to redis')


def on_message(ws, message):
    logger.info(f'Websocket received message: {message}')
    submit()


def on_error(ws, error):
    logger.error(f'Websocket error: {error}')


def on_close(ws, close_status_code, close_msg):
    # Changed from 1 arg to 3 args since websocket-client 1.2.1
    logger.warning(f"### Websocket connection closed: {close_status_code}, {close_msg} ###")


def on_open(ws):
    logger.info("Websocket connected")


def main():
    logger.info('Start main()')
    # Listen to websocket for update notifications
    ws = websocket.WebSocketApp(
        watcherUrl,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open

    # Set websockets to run forever
    # and reconnect while disconnected
    while True:
        # Adds sleep to avoid high CPU load
        time.sleep(1)
        try:
            logger.info(f'Attempt connection to websocket at {watcherUrl}')
            ws.run_forever(
                ping_interval=30,
                ping_timeout=10
            )
        except Exception as e:
            logger.error(e)


if __name__ == '__main__':
    main()
    logger.info('All done.')
