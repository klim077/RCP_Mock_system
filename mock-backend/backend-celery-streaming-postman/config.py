import sys
import os
import datetime
import time
import logging
import pytz
import json

import pika
from bson.json_util import dumps
from celery import Celery

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

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

# def get_secret(secret_name):
#     try:
#         with open(f'/run/secrets/{secret_name}', 'r') as secret_file:
#             return secret_file.read().splitlines()[0]
#     except IOError:
#         raise

# postgres_user = get_secret('SMARTGYM_USER')
# postgres_password = get_secret('SMARTGYM_PASSWORD')
# postgres_db = 'smartgym'
# postgres_ip = 'postgres'
# postgres_machines_table = 'machines'

postgres_user = "postgres"
postgres_password = "a"
postgres_db = "RCP"
postgres_ip = "pgdb"
postgres_machines_table = "machines"

rabbitmq_ip = 'rabbitmq'
rabbitmq_port = 5672
rabbitmq_user = "user"
rabbitmq_pw = "bitnami"

tz_utc = pytz.timezone('UTC')


celeryApp = Celery(
    "postman",
    broker='amqp://user:bitnami@rabbitmq',
)

class PDB:
    def __init__(self, user: str, password: str, db: str, ip: str):
        self.user = user
        self.password = password
        self.db = db
        self.ip = ip

    def __enter__(self):
        self.client = psycopg2.connect(
                        user=self.user, 
                        password=self.password, 
                        dbname=self.db, 
                        host=self.ip
                    )
        self.client.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        del self.client

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