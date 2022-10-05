import os
import time
import datetime
import redis
import json
import pandas as pd
import numpy as np
import requests
from common import logger
from common.config import mongoapi_ip, mongoapi_port, mongoapi_version
from common.utils import rget, j, getRedisChannelAsDict, rowerUpdateRedisFromPostman, getKey, rower_dict
from rower.rower_calculator import WorkoutProcessor
from celery import Celery

rower = WorkoutProcessor()
prev_userID = "dummy-userID"

time.sleep(30)

app = Celery(
    "postman",
    broker='amqp://user:bitnami@rabbitmq',
)

app.conf.task_routes = {
    'compute.#': {'queue': 'compute_queue'},
    'save.#': {'queue': 'saving_queue'},
    'rower.#': {'queue': 'rower_queue'},
    'campaign.#': {'queue': 'campaign_queue'},
}

app.control.add_consumer('rower_queue',
# destination=['worker1'],
destination=['celery@rowerWorker'],
reply=True)

def isUserIdSame(userID: str) -> str:
    global prev_userID

    if (userID != prev_userID):
        prev_userID = userID
        return False
    else:
        return True

@app.task(name='rowerComputation')
def rowerComputation(machineId):
    machineId = json.loads(machineId)

    try:
        logger.info(f'computeRower processing data for machineId in : {machineId}')

        userid = rget(j(machineId, 'user'))
        logger.debug(f'userid: {userid}')

        # channelData = getRedisChannelAsDict(machineId)
        channelData = getKey(machineId["machineId"], rower_dict)
        logger.debug(f'Raw Channel Data: {channelData}')

        if isinstance(channelData, dict):
            rower_workout = rower.rowerCompute(channelData)
            logger.info(f'rower_workout: {rower_workout}')
            res = rowerUpdateRedisFromPostman(machineId["machineId"], rower_workout)
            # logger.info(f'Update Redis enpoint call, result: {res}')
            logger.info(f'rower_workout: {rower_workout}')

    except Exception as e:

        logger.error(f'Error at rowerComputation: {e}')

