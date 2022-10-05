import os
import requests
import datetime
import json
from functools import reduce
import time
import logging
from celery import Celery
import time

import smartgymgatewayutils.config as config
import smartgymgatewayutils.gwHTTP as gwHTTP

# time.sleep(30)

app = Celery(
    "sendWorkout",
    broker='amqp://user:bitnami@rabbitmq',
    backend='rpc://',
)

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
logger = logging.getLogger(__name__)
# logger.setLevel(logging.WARNING)
logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
format_str = '%(levelname)s:%(lineno)s:%(message)s'
formatter = logging.Formatter(format_str)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info('Logger ready')


def on_after_setup_logger(**kwargs):
    logger2 = logging.getLogger('celery')
    logger2.propagate = True
    logger2 = logging.getLogger('celery.app.trace')
    logger2.propagate = True


@app.task(name='getRequest')
def getRequest(url):
    logger.info(f'getRequest({url})')
    try:
        ret = gwHTTP.httpGet(url=url)
        logger.info(f'getRequest {ret}')
        return ret
    except Exception as e:
        logger.error(f'Exception {e} caught on {url}')


@app.task(name='sendWorkout')
def sendWorkout(url, workoutData):
    logger.info(f'workoutData: {workoutData} , Url: {url}')
    try:
        ret = gwHTTP.httpPost(
            url=url,
            data=workoutData
        )
        logger.info(f'sendWorkout {ret}')
        return ret
    except Exception as e:
        logger.error(
            f'Exception caught: {e} onMessage: {workoutData} , Url: {url}'
        )
