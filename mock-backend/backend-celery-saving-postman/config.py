import sys
import os
import datetime
import time
import logging
import pytz

import pika
import redis
from bson.json_util import dumps
from celery import Celery

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
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
# logger.setLevel(logging.WARNING)
# logger.setLevel(logging.ERROR)
ch = logging.StreamHandler()
format_str = '%(levelname)s:%(lineno)s:%(message)s'
formatter = logging.Formatter(format_str)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info('Logger ready')



rabbitmq_ip = 'rabbitmq'
rabbitmq_port = 5672
rabbitmq_user = "user"
rabbitmq_pw = "bitnami"

redis_ip = 'redis'
redis_port = 6379
tz_utc = pytz.timezone('UTC')


celeryApp = Celery(
    "postman",
    broker='amqp://user:bitnami@rabbitmq',
)
r = redis.Redis(host=redis_ip, port=redis_port)

class RMQ:
    def __init__(self, ip: str, port: int, user: str, pw: str):
        self.ip = ip
        self.port = port
        self.user = user
        self.pw = pw
        self.credentials = pika.PlainCredentials(self.user, self.pw)
        self.parameters = pika.ConnectionParameters(
                            self.ip,
                            self.port,
                            '/',
                            self.credentials
                        )

    def __enter__(self):
        self.connection = pika.BlockingConnection(self.parameters)
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()
        del self.connection