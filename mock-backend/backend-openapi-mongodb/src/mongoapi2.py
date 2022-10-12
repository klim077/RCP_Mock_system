from calendar import month
from contextlib import nullcontext
from tabnanny import check
from typing import Optional
from xmlrpc.client import DateTime

from phonenumbers.phonenumberutil import PhoneNumberType
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pymongo
import pytz
from bson.codec_options import CodecOptions
from bson.objectid import ObjectId
import pandas as pd
import datetime
import time
import redis
import flask_bcrypt
import bcrypt
import secrets
import os
import re
import json
import math
import phonenumbers
import logging
from collections import namedtuple
from dateutil import parser
import numpy as np
# from security.aes import encrypt, decrypt
import src.utils.utils as utils
import pika
from bson.json_util import loads, dumps

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
# logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.ERROR)
ch = logging.StreamHandler()
format_str = "%(levelname)s:%(lineno)s:%(message)s"
formatter = logging.Formatter(format_str)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info("Logger ready")


# def get_docker_secret(secret_name):
#     try:
#         with open(f"/run/secrets/{secret_name}", "r") as secret_file:
#             return secret_file.read().splitlines()[0]
#     except IOError:
#         raise


mongo_user = "smartgym"
mongo_password = "password"

# Parameters
postgres_user = "RCP"
postgres_pw = "a"
postgres_db = "RCP"
postgres_ip = "pgdb"
postgres_machines_table = "machines"

mongo_ip = "mongodb"
mongo_port = 27017
db_gym = "gym"
coll_exercise = "exercises"
coll_bodymetrics = "bodymetrics"
coll_leaderboard_metrics = "leaderboard_metrics"
coll_campaigns = "campaigns"
coll_usercampaignstatus = "usercampaignstatus"
coll_users = "users"
coll_apikeys = "apikeys"
coll_accesstokens = "accesstokens"
coll_refreshtokens = "refreshtokens"
coll_wearable_details = "wearabledetails"
coll_wearable_data = "wearabledata"
coll_feedback = "feedback"
coll_feedback_question = "feedback_question"
coll_ban_users = "leaderboard_banned_users"
coll_aht_checkin_data = "aht_checkin_data"
coll_aht_trails_data = "aht_trails"
coll_aht_checkpoint_details = "aht_checkpoint_details"

tz_sg = pytz.timezone("Singapore")
tz_utc = pytz.timezone("UTC")
options = CodecOptions(tz_aware=True, tzinfo=tz_utc)

redis_ip = "redis"
redis_port = 6379
create_user_channel = 'create-user'
channel_weighingscale = "weighingscale-metrics"
channel_weightstack = "weightstack-computation"
channel_bike = "spinningbike-computation"
channel_campaign_calculation = "campaign-computation"
channel_bodyweight = "bodyweight-computation"
channel_bpm = "bpm-measurement"
channel_rower = "rower-computation"
r = redis.Redis(host=redis_ip, port=redis_port)

rabbitmq_ip = 'rabbitmq'
rabbitmq_port = 5672
rabbitmq_user = "user"
rabbitmq_pw = "bitnami"
rabbitmq_streaming_queue = "stream"
rabbitmq_saving_queue = "save"
rabbitmq_processing_queue = "process"

gender_variables = ["Male", "Female"]


class PDB:
    def __init__(self, user: str, pw: str, db: str, ip: str):
        self.user = user
        self.pw = pw
        self.db = db
        self.ip = ip

    def __enter__(self):
        self.client = psycopg2.connect(
            user=self.user, password=self.pw, database=self.db, host=self.ip
        )
        self.client.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        del self.client


class MDB:
    def __init__(self, ip: str, port: int, username: str, password: str):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

    def __enter__(self):
        from pymongo import MongoClient
        self.client = MongoClient(
            self.ip, self.port, username=self.username, password=self.password)
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


def milliseconds_since_epoch_to_datetime(millisecondsSinceEpoch):
    return datetime.datetime.utcfromtimestamp(millisecondsSinceEpoch / 1000)


def validate_datetime(body):
    if "exercise_started" in body:
        body["exercise_started"] = milliseconds_since_epoch_to_datetime(
            body["exercise_started"]
        )

    if "exercise_ended" in body:
        body["exercise_ended"] = milliseconds_since_epoch_to_datetime(
            body["exercise_ended"]
        )

    if "last_modified" in body:
        body["last_modified"] = milliseconds_since_epoch_to_datetime(
            body["last_modified"]
        )

    if "start_date" in body:
        body["start_date"] = milliseconds_since_epoch_to_datetime(
            body["start_date"])

    if "end_date" in body:
        body["end_date"] = milliseconds_since_epoch_to_datetime(
            body["end_date"])

    if "created" in body:
        body["created"] = milliseconds_since_epoch_to_datetime(body["created"])
    else:
        body["created"] = datetime.datetime.now(tz=tz_utc)

    if "exercise_data" in body and isinstance(body["exercise_data"], list):
        for idx, ele in enumerate(body["exercise_data"]):
            body["exercise_data"][idx][
                "timestamp"
            ] = milliseconds_since_epoch_to_datetime(ele["timestamp"])

    return body


def get_machines():
    query = "SELECT uuid, type, exercise_name, exercise_group FROM machines"
    with PDB(postgres_user, postgres_pw, postgres_db, postgres_ip) as conn:
        c = conn.cursor()
        c.execute(query)
        result = c.fetchall()

    result_json = [
        {
            "uuid": ele[0],
            "type": ele[1],
            "exercise_name": ele[2],
            "exercise_group": ele[3],
        }
        for ele in result
    ]

    return result_json


def get_location():
    query = "SELECT DISTINCT location FROM machines"
    with PDB(postgres_user, postgres_pw, postgres_db, postgres_ip) as conn:
        c = conn.cursor()
        c.execute(query)
        result = c.fetchall()

    result_json = []
    for ele in result:
        result_json.append(
            {
                "location": ele[0],
            }
        )

    return result_json


def get_machines_by_location(location: str):
    # Query is case insensitive
    query = f"SELECT uuid, name, type, location FROM machines \
            WHERE LOWER(location)=LOWER('{location}')"
    with PDB(postgres_user, postgres_pw, postgres_db, postgres_ip) as conn:
        c = conn.cursor()
        c.execute(query)
        r = [dict((c.description[i][0], value)
                  for i, value in enumerate(row)) for row in c.fetchall()]

    return r


def get_machine_info_by_id(uuid: str):
    query = f"SELECT * FROM machines \
            WHERE uuid='{uuid}'"
    with PDB(postgres_user, postgres_pw, postgres_db, postgres_ip) as conn:
        c = conn.cursor()
        c.execute(query)
        row = c.fetchall()[0]
        cols = [column[0] for column in c.description]

    return dict(zip(cols, row))

def validate_machine_id(machine_id: str) -> bool:
    """Validates if machine_id is in database.

    Args:
        machine_id (str): Machine Id
    Returns:
        bool: True is exists else False
    """
    logger.debug(f"validate_machine_id()")

    # Validate against machine list
    machines = get_machines()
    machine_ids = [machine["uuid"] for machine in machines]

    return machine_id in machine_ids


def dispatch_machine(machineId: str) -> str:
    """Handler for /machine/{machineId}/dispatch

    Args:
      user: Authenticated user
      machineId: Requested machine id
    Returns:
      str: Dispatch status
    """

    logger.debug(f"dispatch_machine start")

    # Validate input
    # 32 characters within [a-f0-9]
    pattern = "^[a-f0-9]{32}$"
    pattern_check = re.match(pattern, machineId)

    if not pattern_check:
        msg = f"Bad request: {machineId}"
        # logger.info(msg)
        return msg

    # Validate against machine list
    if not validate_machine_id(machineId):
        msg = f"Bad request: {machineId}"
        # logger.info(msg)
        return msg

    with RMQ(rabbitmq_ip, rabbitmq_port, rabbitmq_user, rabbitmq_pw) as conn:
        channel = conn.channel()
        # channel.queue_delete(queue=queue)
        channel.queue_declare(queue=rabbitmq_saving_queue, durable=True)
        channel.basic_publish(exchange='',
                              routing_key=rabbitmq_saving_queue,
                              body=machineId,
                              properties=pika.BasicProperties(
                                  delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
                              )
        msg = f"Dispatched machine {machineId} to {rabbitmq_saving_queue} rabbitmq queue"

    logger.info(msg)

    return msg

def dispatch_rower(machineId):

    logger.debug("dispatch_rower start")

    payloadData = {"machineId": machineId}
    payloadData = json.dumps(payloadData)

    revert = bool(os.getenv('REVERT_STAGE1', False))
    if revert:
        numof_subs = r.publish(channel_rower, payloadData)
        msg = f"Dispatched rower {machineId} to {numof_subs} subscribers"
    else:
        with RMQ(rabbitmq_ip, rabbitmq_port, rabbitmq_user, rabbitmq_pw) as conn:
            channel = conn.channel()
            # channel.queue_delete(queue=queue)
            channel.queue_declare(queue=rabbitmq_streaming_queue, durable=True)
            channel.basic_publish(exchange='',
                                  routing_key=rabbitmq_streaming_queue,
                                  body=payloadData,
                                  properties=pika.BasicProperties(
                                      delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
                                  )
            msg = f"Dispatched machine {machineId} to {rabbitmq_streaming_queue} rabbitmq queue"

    logger.info(msg)
    return msg

def convertStringtoArray(text: str):
    result = list(text.split(","))
    return result


def get_keyvalues(machineId: str):
    """Get selected keys for a machine from redis

    Args:
      machineId: Machine id
    Returns:
      Dict of selected keys with values
    """

    # Selected keys
    keys = [
        "w0",
        "wn",
        "wa",
        "user",
        "weight",
        "available",
        "name",
        "altitude",
        "inclination",
        "location",
        "reps",
        "sets",
        "type",
        "calories",
        "speed",
        "cadence",
        "rec",
        "distance",
        "calories",
        "power",
        "avgCadence",
        "avgSpeed",
        "workoutTime",
        "exercise_group",
        "exercise_name",
        "is_ippt",
        "keypoints",
        "bodylandmarks",
        "met_instant",
        "met_sum",
        "strokes",
        "timestamp",
        "pace",
        "rowingTime",
        "heartRate",
        "interval",
    ]

    # Sanitize inputs
    machineId = machineId.strip()

    # Pad with machineId
    full_keys = ["{}:{}".format(machineId, ele) for ele in keys]

    # Get multiple keys
    values = r.mget(full_keys)
    # print(values)

    # Make return value
    out = {}
    for k, v in zip(keys, values):
        if v:
            out[k] = v.decode()

        else:
            out[k] = v
    """for lift fitness equipment"""
    try:
        out["w0"] = float(out["w0"])
        out["wn"] = float(out["wn"])
        out["wa"] = convertStringtoArray(str(out["wa"]))

    except:
        out["wn"] = 0
        out["w0"] = 0
        out["wa"] = 0

    out["name"] = out["name"]
    out["location"] = out["location"]
    out["type"] = out["type"]

    if out["available"] != None:
        out["available"] = bool(int(out["available"]))

    if out["user"] != None:
        out["user"] = out["user"]

    if out["weight"] != None:
        out["weight"] = float(out["weight"])

    if out["reps"] != None:
        out["reps"] = int(out["reps"])

    if out["sets"] != None:
        out["sets"] = str(out["sets"])

    if out["calories"] != None:
        out["calories"] = float(out["calories"])

    if out["speed"] != None:
        out["speed"] = float(out["speed"])

    if out["cadence"] != None:
        out["cadence"] = float(out["cadence"])

    if out["rec"] != None:
        out["rec"] = out["rec"]

    if out["distance"] != None:
        out["distance"] = float(out["distance"])

    if out["calories"] != None:
        out["calories"] = float(out["calories"])

    if out["power"] != None:
        out["power"] = float(out["power"])

    if out["avgCadence"] != None:
        out["avgCadence"] = float(out["avgCadence"])

    if out["avgSpeed"] != None:
        out["avgSpeed"] = float(out["avgSpeed"])

    if out["workoutTime"] != None:
        out["workoutTime"] = float(out["workoutTime"])

    if out["altitude"] != None:
        out["altitude"] = float(out["altitude"])

    if out["inclination"] != None:
        out["inclination"] = float(out["inclination"])

    if out["exercise_group"] != None:
        out["exercise_group"] = str(out["exercise_group"])

    if out["exercise_name"] != None:
        out["exercise_name"] = str(out["exercise_name"])

    if out["is_ippt"] != None:
        out["is_ippt"] = str(out["is_ippt"])

    if out["keypoints"] != None:
        out["keypoints"] = str(out["keypoints"])

    if out["bodylandmarks"] != None:
        out["bodylandmarks"] = out["bodylandmarks"]

    if out["strokes"] != None:
        out["strokes"] = float(out["strokes"])

    if out["timestamp"] != None:
        out["timestamp"] = float(out["timestamp"])

    if out["pace"] != None:
        out["pace"] = float(out["pace"])

    if out["rowingTime"] != None:
        out["rowingTime"] = float(out["rowingTime"])

    if out["heartRate"] != None:
        out["heartRate"] = float(out["heartRate"])

    if out["interval"] != None:
        out["interval"] = float(out["interval"])

    return out


def set_key(machineId: str, key: str, body: dict):
    """Set key for a machine in redis

    Args:
      machineId: Machine id
      key: Key to set
      body: Dict containing value to set
    Returns:
      True is success, False otherwise
    """

    logger.debug(f"set_key()")

    value = body["value"]

    k, v = "", ""
    if key == "reps":
        k = f"{machineId}:reps"
        v = int(value)
    if key == "weight":
        k = f"{machineId}:weight"
        v = float(value)
    if key == "available":
        k = f"{machineId}:available"
        v = int(bool(int(value)))
    if key == "user":
        k = f"{machineId}:user"
        v = value
    if key == "avgCadence":
        k = f"{machineId}:avgCadence"
        v = float(value)
    if key == "avgSpeed":
        k = f"{machineId}:avgSpeed"
        v = float(value)
    if key == "cadence":
        k = f"{machineId}:cadence"
        v = float(value)
    if key == "power":
        k = f"{machineId}:power"
        v = float(value)
    if key == "speed":
        k = f"{machineId}:speed"
        v = float(value)
    if key == "distance":
        k = f"{machineId}:distance"
        v = float(value)
    if key == "met_sum":
        k = f"{machineId}:met_sum"
        v = float(value)
    if key == "met_instant":
        k = f"{machineId}:met_instant"
        v = float(value)
    if key == "calories":
        k = f"{machineId}:calories"
        v = float(value)
    if key == "rec":
        k = f"{machineId}:rec"
        v = value
    if key == "workoutTime":
        k = f"{machineId}:workoutTime"
        v = float(value)
    if key == "altitude":
        k = f"{machineId}:altitude"
        v = float(value)
    if key == "inclination":
        k = f"{machineId}:inclination"
        v = float(value)
    if key == "total_speed":
        k = f"{machineId}:total_speed"
        v = float(value)
    if key == "total_cadence":
        k = f"{machineId}:total_cadence"
        v = float(value)
    if key == "pedal":
        k = f"{machineId}:pedal"
        v = int(value)
    if key == "exercise_group":
        k = f"{machineId}:exercise_group"
        v = str(value)
    if key == "exercise_name":
        k = f"{machineId}:exercise_name"
        v = str(value)
    if key == "is_ippt":
        k = f"{machineId}:is_ippt"
        v = str(value)
    if key == "bodylandmarks":
        k = f"{machineId}:bodylandmarks"
        v = value
    if key == "strokes":
        k = f"{machineId}:strokes"
        v = float(value)
    if key == "timestamp":
        k = f"{machineId}:timestamp"
        v = float(value)
    if key == "pace":
        k = f"{machineId}:pace"
        v = float(value)
    if key == "type":
        k = f"{machineId}:type"
        v = str(value)
    if key == "rowingTime":
        k = f"{machineId}:rowingTime"
        v = float(value)
    if key == "heartRate":
        k = f"{machineId}:heartRate"
        v = float(value)
    if key == "interval":
        k = f"{machineId}:interval"
        v = float(value)

    logger.debug(f"{k}, {v}")
    r.set(k, v)

    return True


def del_key(machineId: str, key: str):
    """Delete key for a machine in redis

    Args:
      machineId: Machine id
      key: Key to delete
    Returns:
      True is success, False otherwise
    """

    logger.debug(f"del_key()")

    k = ""
    if key == "user":
        k = f"{machineId}:user"
    if key == "data_stream":
        k = f"{machineId}:data_stream"

    # logger.debug(f'{k}')
    r.delete(k)

    return True


def increment_key(machineId: str, key: str, body: dict):
    """Increment value of key for a machine in redis

    Args:
      machineId: Machine id
      key: Key to set
      body: Dict containing value to set
    Returns:
      True is success, False otherwise
    """

    logger.debug(f"increment_key()")

    value = body["value"]

    k, v = "", ""
    if key == "reps":
        k = f"{machineId}:reps"
        v = int(value)
        r.incr(k, v)
    if key == "met_sum":
        k = f"{machineId}:met_sum"
        v = float(value)
        r.incrbyfloat(k, v)
    if key == "calories":
        k = f"{machineId}:calories"
        v = float(value)
        r.incrbyfloat(k, v)
    if key == "distance":
        k = f"{machineId}:distance"
        v = float(value)
        r.incrbyfloat(k, v)
    if key == "workoutTime":
        k = f"{machineId}:workoutTime"
        v = float(value)
        r.incrbyfloat(k, v)
    if key == "altitude":
        k = f"{machineId}:altitude"
        v = float(value)
        r.incrbyfloat(k, v)
    if key == "total_speed":
        k = f"{machineId}:total_speed"
        v = float(value)
        r.incrbyfloat(k, v)
    if key == "total_cadence":
        k = f"{machineId}:total_cadence"
        v = float(value)
        r.incrbyfloat(k, v)
    if key == "pedal":
        k = f"{machineId}:pedal"
        v = int(value)
        r.incr(k, v)

    # logger.debug(f'{k}, {v}')

    return True


def xadd(machineId: str, key: str, body: dict):
    """Adds an item to redis stream at [key]

    Args:
      machineId: Machine id
      key: Redis stream key
      body: Dict to add
    Returns:
      True is success, False otherwise
    """

    logger.debug(f"xadd()")

    k = f"{machineId}:{key}"
    v = body
    r.xadd(k, v)

    return True


def xlen(machineId: str, key: str):
    """check lens of an item in redis stream at [key]

    Args:
      machineId: Machine id
      key: Redis stream key
    Returns:
      count value or 0
    """
    logger.debug(f"xadd()")

    k = f"{machineId}:{key}"

    result = r.xlen(k)

    return result

