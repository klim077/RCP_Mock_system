import abc
import os
import time
import json
from json.decoder import JSONDecodeError
from queue import Queue
from threading import Thread

import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from . import config
from . import gwMQTT as mqtt
from . import gwOrchestrator as orchestrator
from . import gwHTTP
from . import gwAvailability
from . import gwLogger
from celery import Celery


celeryApp = Celery(
    "sendWorkout",
    broker='amqp://user:bitnami@rabbitmq',
    backend='rpc://',
)


# Helper Functions
def timestamp():
    return time.time()


# Get hostname
hostname = os.environ['HOSTNAME']

# Variables
apikey = config.api_key
serverUrl = config.server_url

redis_ip_local = config.local_redis_ip
redis_port_local = config.local_redis_port

mqtt_ip = config.broker_address
mqtt_port = config.broker_port


class AbsWorkout(metaclass=abc.ABCMeta):
    def __init__(self, machine_type):
        # Set up logger
        print("Machine type: ", machine_type)
        loggerName = '{}_{}'.format(machine_type, hostname)
        gwLogger.loggerWrapper.start(loggerName)

        gwLogger.logger.info('{} logger ready'.format(machine_type))

        self.workoutQueue = Queue(maxsize=0)

        self.serverUrl = config.server_url

        self.machineID = orchestrator.acquireMachineId(
            ip=redis_ip_local,
            port=redis_port_local,
            hostname=hostname,
            machine_type=machine_type,
        )
        print("machine ID acquired : ", self.machineID)

        self.mqtt_uuid = f'control_{machine_type}_{timestamp()}'
        mqtt_sub_topic = self.machineID + "/data"

        self.mqtt_client = mqtt.MQTTWrapper(self.mqtt_uuid)
        self.mqtt_client.setup(mqtt_ip, mqtt_port)
        self.mqtt_client.subscribeMqtt(mqtt_sub_topic)

        pass

    def updateRedis(self, workoutData, endpoint):
        self.workoutUrl = serverUrl + '/v0.1/machines/' + \
            self.machineID + '/' + endpoint
        ret = gwHTTP.httpPost(
            url=self.workoutUrl,
            data=workoutData
        )

    def MQTTListener(self):
        print("Starting MQTT listening Thread")

        while True:
            msg_str, _ = self.mqtt_client.next(1 / 20)
            # Decode JSON
            try:
                msg_dict = json.loads(msg_str)
            except JSONDecodeError as e:
                print(e)
            # Extract variables
            try:
                self.processWorkout(msg_dict)
            except KeyError as e:
                print(e)

    def addWorkoutDataToQueue(
        self,
        workoutData,
        endpoint,
        isWeighingScale=False,
        isBpm=False,
        isPulseOx=False
    ):
        if not isWeighingScale and not isBpm and not isPulseOx:
            self.workoutUrl = serverUrl + '/v0.1/machines/' + \
                self.machineID + '/' + endpoint
        elif isBpm:
            self.workoutUrl = serverUrl + '/v0.1/bpm/' + \
                self.machineID + '/' + endpoint
        elif isWeighingScale:
            self.workoutUrl = serverUrl + '/v0.1/weighingScales/' + \
                self.machineID + '/' + endpoint
        elif isPulseOx:
            self.workoutUrl = serverUrl + '/v0.1/pulseox/' + \
                self.machineID + '/' + endpoint
        else:
            gwLogger.logger.error("machine not defined")
        celeryApp.send_task('sendWorkout', (self.workoutUrl, workoutData))

    def sendGetRequest(self, url):
        print(f'AbsWorkout sendGetRequest({url})')
        task = celeryApp.send_task('getRequest', (url,))
        result = task.get()
        print(f'AbsWorkout sendGetRequest {result}')
        return result

    @abc.abstractmethod
    def processWorkout(self, msg_dict):
        pass

    def startController(self):
        self.MQTTListener()
