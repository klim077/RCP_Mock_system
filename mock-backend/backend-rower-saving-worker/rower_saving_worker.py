import os
from random import setstate
import redis
import requests
import pytz
import datetime
import json
import pandas as pd
from functools import reduce
import socket
import sys
import time
import numpy as np
import pickle
import math

from bson.json_util import loads, dumps

from machine_classes import Exercise, ExerciseDetail, BodyMetrics, Rower

from celery import Celery

time.sleep(30)

## Set up logger
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)
logger.info('Logger ready')

mongoapi_ip = 'openapi-mongodb'
mongoapi_port = 9090
mongoapi_version = 'v0.1'
# Datetime
tz_sg = pytz.timezone('Singapore')

# def get_secret(secret_name):
#     try:
#         with open(f'/run/secrets/{secret_name}', 'r') as secret_file:
#             return secret_file.read().splitlines()[0]
#     except IOError:
#         raise

# headers = {
#     'X-API-Key': get_secret('APIKey'),
# }

redis_ip = 'redis'
redis_port = 6379
r = redis.Redis(host=redis_ip, port=redis_port)
create_exercise_channel = 'create-exercise'


app = Celery(
    "postman",
    broker='amqp://user:bitnami@rabbitmq',
)

@app.task(name='save_rower_exercise')
def save_rower_exercise(payload_data):
    payload_data = loads(payload_data)
    try:
        exerciseDetails, user_info = saveBasicInformation(payload_data)
        exercises = process(exerciseDetails, payload_data)
        # Post to mongoDB
        for exercise in exercises:
            post(exercise)

        # Publish notification that workout has been saved
        # Subscribers:
        # - socket-io
        # - campaign-status-calculator
        payload_data = {
            "location": payload_data['location'],
            "user_id": payload_data['user'],
            "message": 'posted'
        }
        payload_data = json.dumps(payload_data)
        numof_subs = r.publish(exerciseDetails.userid, payload_data)

        # publish to stage-3 trigger
        payload = dumps(payload_data)
        numof_subs = r.publish(create_exercise_channel, payload)

        logger.info('Published to {} subscribers'.format(numof_subs))
        return "Success"

    except Exception as e:
        logger.error('Exception caught: {}'.format(e))



def saveBasicInformation(payload_data):
    machineId = payload_data['uuid']
    userid = payload_data['user']
    if not userid:
        raise ValueError(f'No user at machine {machineId}')

    user_info = getUserInfo(userid)

    exerciseDetail = ExerciseDetail(
        payload_data['uuid'],
        payload_data['user'],
        user_info['user_gender'],
        user_info['user_display_name'],
        payload_data['name'],
        payload_data['location'],
        payload_data['type']
    )
    return exerciseDetail, user_info


def getUserInfo(userid):
    url = 'http://{ip}:{port}/{ver}/users/{userId}'.format(
        ip=mongoapi_ip,
        port=mongoapi_port,
        ver=mongoapi_version,
        userId=userid
    )
    logger.debug(url)

    response = requests.get(
        url=url,
        # headers=headers,
    )

    if response.ok:
        logger.info('getUserInfo status_code: {}'.format(response.status_code))
        return response.json()
    else:
        logger.error('getUserInfo status_code: {}, {}'.format(
            response.status_code, response.text))
        # TODO: What to return?
        return

def process(exerciseDetail, payload_data):
    # Get exercise specific data
    data_stream = payload_data['data_stream']

    # Process exercise specific data
    exercise = exerciseDetail.exerciseType

    logger.info('Processing {}'.format(exercise))

    # TODO: Add exercise rower processing
    logger.info("Rower Stream Received")
    processed = processExerciseRower(data_stream)

    # Prepare return value
    out = makeExercises(exerciseDetail, processed)

    # Return list of exercises
    return out

def processExerciseRower(input):
    out = []
    # rower_list =[]
    # Make into dataframe
    df = pd.DataFrame(input)

    # fileName = "./dataStream" + "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # df.to_pickle(fileName)
    # Make timestamp index and also preserve it as a column
    col_list = ['distance', 'cadence', 'calories', 'strokes', 'timestamp', 'workoutTime', 'pace', 'power']

    logger.debug(df.columns)

    for col in col_list:
        df[col] = pd.to_numeric(df[col])

    for ix, row in df.iterrows():
        _rower = Rower(distance=row.distance,
                                 cadence=row.cadence, 
                                 calories=row.calories,
                                 strokes=row.strokes,
                                 timestamp=row.timestamp,
                                 workoutTime=row.workoutTime,
                                 pace=row.pace,
                                 power=row.power
                                 )
        out.append(_rower)

    # logger.debug(df.loc[-1,"workoutTime"])
    logger.info("Created Exercise RowerObjects List")

    return out


def makeExercises(exerciseDetails, input):
    # Get basic information
    userid = exerciseDetails.userid
    gender = exerciseDetails.gender
    nickname = exerciseDetails.nickname
    name = exerciseDetails.name
    location = exerciseDetails.location
    exercise = exerciseDetails.exerciseType
    machineId = exerciseDetails.machineId

    out = []
    ex = None
    
    # Build Summary
    logger.debug("rowerdata input len:{}".format(len(input)))
    timeStarted = input[0].timestamp
    calories = input[0].calories
    logger.debug('{} {}'.format(timeStarted, calories))

    # First Rower Object
    sb1 = input[0].timestamp
    sb2 = input[len(input) - 1].timestamp
    duration = (sb2 - sb1).seconds
    woDuration = reduce(
        lambda x, y: x + y, map(lambda x: x.workoutTime, input))
    logger.debug("Rower Duration {}, workoutDuration: {}".format(
        duration, woDuration))

    # avg_cadence = 0
    # avg_speed = 0
    # for st_rower in input:
    #     avg_cadence = avg_cadence + st_rower.cadence
    #     avg_speed = avg_speed + st_rower.speed

    # avg_cadence = avg_cadence / len(input)
    # avg_speed = avg_speed / len(input)

    total_cals = input[-1].calories
    total_distance = input[-1].distance

    logger.debug("totalDis: {}".format(total_distance))
    logger.debug("totalCals: {}".format(total_cals))

    summary = {
        'total_distance': total_distance,
        'duration': duration,
        # 'avg_speed': avg_speed,
        # 'avg_cadence': avg_cadence,
        'calories': total_cals,
        'workoutDuration': woDuration
    }

    logger.debug("Summary: {}".format(summary))

    ex = Exercise(
        userid=userid,
        nickname=nickname,
        gender=gender,
        machineid=machineId,
        name=name,
        location=location,
        exercise=exercise,
        timeStarted=timeStarted,
        timeEnded=sb2,
        data=input,  # Exercise object
        summary=summary
    )

    out.append(ex)

    return out

def post(exercise):
    logger.info('Posting {}'.format(exercise.to_dict()))

    url = 'http://{ip}:{port}/{ver}/exercises'.format(
        ip=mongoapi_ip,
        port=mongoapi_port,
        ver=mongoapi_version
    )

    response = requests.post(
        url=url,
        # headers=headers,
        json=exercise.to_dict()
    )

    if response.ok:
        logger.info('post status_code: {}'.format(response.status_code))
    else:
        logger.error('post status_code: {}, {}'.format(
            response.status_code, response.text))