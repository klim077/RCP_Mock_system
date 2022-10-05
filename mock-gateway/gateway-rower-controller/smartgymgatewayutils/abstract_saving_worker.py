import abc
import os
import pytz
import redis
import requests
import json
from . import config
from bson.json_util import loads, dumps
# from . import gwLogger


#class 
class ExerciseDetail:
    def __init__(self, machineId, userid, gender, nickname, name, location, exerciseType):
        self.machineId = machineId
        self.userid = userid
        self.gender = gender
        self.nickname = nickname
        self.name = name
        self.location = location
        self.exerciseType = exerciseType
        #self.user_gender = user_gender.lowercase()

# Helper Functions
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)
logger.info('Logger ready')


# Get hostname
hostname = os.environ['HOSTNAME']

# Variables
# apikey = config.api_key
server_url = config.server_url
# server_url = '192.168.1.119:22090/v0.1/ui/'

redis_ip = 'redis'
redis_port = 6379
r = redis.Redis(host=redis_ip, port=redis_port)

mongoapi_ip = 'openapi-mongodb'
mongoapi_port = 9090
mongoapi_version = 'v0.1'
# Datetime
tz_sg = pytz.timezone('Singapore')
create_exercise_channel = 'create-exercise'

# def get_secret(secret_name):
#     try:
#         with open(f'/run/secrets/{secret_name}', 'r') as secret_file:
#             return secret_file.read().splitlines()[0]
#     except IOError:
#         raise

# headers = {
#     'X-API-Key': get_secret('APIKey'),
# }

def post(exercise):
    # gwLogger.logger.info('Posting {}'.format(exercise.to_dict()))

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
        # gwLogger.logger.info('post status_code: {}'.format(response.status_code))
        logger.info("response from post endpoint")
        logger.info(response.json())
        return response.json()
        pass
    else:
        # gwLogger.logger.error('post status_code: {}, {}'.format(
            # response.status_code, response.text))
        pass

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

class Abs_saving_worker(metaclass=abc.ABCMeta):
    def __init__(self, machine_type, payload_data):
        # Set up logger
        loggerName = '{}_{}'.format(machine_type, hostname)
        # gwLogger.loggerWrapper.start(loggerName)

        # gwLogger.logger.info('{} logger ready'.format(machine_type))
        self.exercise_ids = []
        self.exercises = []
        self.exercise_details = {}
        self.user_info = {}
        #load data
        self.payload_data = loads(payload_data)

        self.server_url = server_url


        pass


    def post_workout(self):

        #set exercise details
        self.exercise_details, self.user_info = saveBasicInformation(self.payload_data)
        #process data
        self.exercises = self.process_workout()
        #post workout data
        try:
            for exercise in self.exercises:
                response = post(exercise)
                self.exercise_ids.append(response)
            self.__send_redis_update()
        except Exception as e:
            # gwLogger.logger.error('post workout exception caught: {}'.format(e))
            logger.error('post workout exception caught: {}'.format(e))
            pass
    
    def __send_redis_update(self):
        try:
            redis_payload_data = {
            "location": self.payload_data['location'],
            "user_id": self.payload_data['user'],
            "exercise_ids": self.exercise_ids,
            "message": 'posted'
        }
            #Update frontend when saving completed
            payload_data = json.dumps(redis_payload_data)
            numof_subs = r.publish(self.exercise_details.userid, payload_data)
            #publish to stage-3 trigger
            payload = dumps(redis_payload_data)
            logger.info(payload)
            numof_subs = r.publish(create_exercise_channel, payload)
            # gwLogger.logger.info('Published to {} subscribers'.format(numof_subs))
            logger.info('Published to {} subscribers'.format(numof_subs))
            return "Success"
        except Exception as e:
            # gwLogger.logger.error('send redis exception caught: {}'.format(e))
            logger.error('send redis exception caught: {}'.format(e))
            pass

    @abc.abstractmethod
    def process_workout(self):
        pass

 
