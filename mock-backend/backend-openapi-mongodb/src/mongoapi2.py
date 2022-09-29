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
from security.aes import encrypt, decrypt
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


def get_docker_secret(secret_name):
    try:
        with open(f"/run/secrets/{secret_name}", "r") as secret_file:
            return secret_file.read().splitlines()[0]
    except IOError:
        raise


mongo_user = get_docker_secret('SMARTGYM_USER')
mongo_password = get_docker_secret('SMARTGYM_PASSWORD')

# Parameters
postgres_user = get_docker_secret("SMARTGYM_USER")
postgres_pw = get_docker_secret("SMARTGYM_PASSWORD")
postgres_db = "smartgym"
postgres_ip = "postgres"
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


def mongoGetBodyMetricsList(
    user_id, exercise_name="Weighing Scale", sort_date_by="DESC", limit=0, location="", start_date=0, end_date=0
):

    if start_date < 0 or end_date < 0:
        return {"error": "Bad request, Invalid date input"}
    if start_date > end_date and end_date > 0:
        return {"error": "Bad request, Invalid date range"}

    queryParams = []
    queryParams.append({"user_id": user_id})
    queryParams.append({'exercise_name': exercise_name})

    if location != "":
        queryParams.append({"exercise_location": location})
    if start_date != 0:
        queryParams.append(
            {"created": {
                "$gte": milliseconds_since_epoch_to_datetime(start_date)}}
        )
    if end_date != 0:
        queryParams.append(
            {"created": {
                "$lt": milliseconds_since_epoch_to_datetime(end_date)}}
        )

    query = {"$match": {"$and": queryParams}}

    # Parse date sort
    if sort_date_by == "DESC":
        mongo_sort = pymongo.DESCENDING
    elif sort_date_by == "ASC":
        mongo_sort = pymongo.ASCENDING
    else:
        mongo_sort = pymongo.DESCENDING

    # Sort
    sort = {"$sort": {"date": mongo_sort}}

    # Limit
    limit_arg = {"$limit": limit}

    pipeline = []
    pipeline.append(query)
    pipeline.append(sort)
    if limit != 0:
        pipeline.append(limit_arg)

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_bodymetrics, codec_options=options)
        # cur = coll.find(query).sort('created', mongo_sort).limit(limit)
        cur = coll.aggregate(pipeline)

    cur_list = list(cur)

    for elem in cur_list:
        elem["_id"] = str(elem["_id"])

    if cur_list:
        return {"res": cur_list}
    else:
        return {"error": "Not found"}


def mongoGetBpMetricsList(
    user_id, exercise_name, sort_date_by="DESC", limit=0, location="", start_date=0, end_date=0
):

    if start_date < 0 or end_date < 0:
        return {"error": "Bad request, Invalid date input"}
    if start_date > end_date and end_date > 0:
        return {"error": "Bad request, Invalid date range"}

    queryParams = []
    queryParams.append({"user_id": user_id})
    queryParams.append({'exercise_name': exercise_name})

    if location != "":
        queryParams.append({"exercise_location": location})
    if start_date != 0:
        queryParams.append(
            {"created": {
                "$gte": milliseconds_since_epoch_to_datetime(start_date)}}
        )
    if end_date != 0:
        queryParams.append(
            {"created": {
                "$lt": milliseconds_since_epoch_to_datetime(end_date)}}
        )

    query = {"$match": {"$and": queryParams}}

    # Parse date sort
    if sort_date_by == "DESC":
        mongo_sort = pymongo.DESCENDING
    elif sort_date_by == "ASC":
        mongo_sort = pymongo.ASCENDING
    else:
        mongo_sort = pymongo.DESCENDING

    # Sort
    sort = {"$sort": {"date": mongo_sort}}

    # Limit
    limit_arg = {"$limit": limit}

    pipeline = []
    pipeline.append(query)
    pipeline.append(sort)
    if limit != 0:
        pipeline.append(limit_arg)

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_bodymetrics, codec_options=options)
        # cur = coll.find(query).sort('created', mongo_sort).limit(limit)
        cur = coll.aggregate(pipeline)

    cur_list = list(cur)

    for elem in cur_list:
        elem["_id"] = str(elem["_id"])

    if cur_list:
        return {"res": cur_list}
    else:
        return {"error": "Not found"}


def validate_phone_number(phone_number: str) -> Optional[str]:
    """Validates a phone number.

    Args:
        phone_number (str): Phone number
    Returns:
        str: Phone number in E164 format
    """
    logger.info(f"validate_phone_number")

    # Parse phone number
    try:
        number = phonenumbers.parse(
            number=phone_number,
            region="SG",
        )
    except phonenumbers.phonenumberutil.NumberParseException as _:
        logger.warning(f"Invalid phone number")
        return None

    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def find_user_by_phone_number(phone_number: str) -> Optional[str]:
    """Finds a user by phone number.

    Args:
        phone_number (str): Phone number
    Returns:
        str: User
    """
    logger.info(f"find_user_by_phone_number")

    # Validate input
    number = validate_phone_number(phone_number=phone_number)
    if not number:
        return None

    # Construct query
    # [national_number] is <int>
    parsed_number = phonenumbers.parse(
        number=number,
    )
    query = {"user_phone_no": str(parsed_number.national_number)}
    projection = {"_id": 1}

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_users,
        )
        res = coll.find_one(
            query,
            projection,
        )
    if res:
        return str(res["_id"])
    else:
        return None


def get_user(user, userId):
    # Query user
    # query = {'user_nickname': userId}
    logger.info(f"get_user")

    # TODO: Implement user query
    # Query user
    try:
        query = {"_id": ObjectId(userId)}
    except Exception:
        return {"error": "Bad userId"}

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_users, codec_options=options)
        res = coll.find_one(query)
    result = {}
    logger.info(res["user_phone_no"])
    logger.info(decrypt(res["user_phone_no"]))
    if res:
        if "username" in res:
            result.update({"username": res["username"]})
        if "user_display_name" in res:
            result.update({"user_display_name": res["user_display_name"]})
        if "user_id" in res:
            result.update({"user_id": res["user_id"]})
        if "user_registered" in res:
            result.update({"user_registered": res["user_registered"]})
        if "user_gender" in res:
            result.update({"user_gender": res["user_gender"]})
        if "user_phone_no" in res:
            phone_no = decrypt(res["user_phone_no"])
            result.update({"user_phone_no": phone_no})
        if "user_height" in res:
            result.update({"user_height": res["user_height"]})
        if "user_dob" in res:
            result.update({"user_dob": res["user_dob"]})
        if "user_weight" in res:
            result.update({"user_weight": res["user_weight"]})
        if "56km_challenge" in res:
            result.update({"56km_challenge": res["56km_challenge"]})

        return result
    else:
        return {"error": "userId not found"}


def delete_user(user, userId):
    logger.info(f"delete_user")

    try:
        query_user = {"_id": ObjectId(userId)}  # Query user
        query_exercise = {"user_id": userId}  # Query exercises by user
    except Exception:
        return {"error": "Bad userId"}

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll_user = db.get_collection(
            coll_users,
            # codec_options=options
        )
        res_user = coll_user.delete_one(query_user)  # delete user with userId
        coll_exercises = db.get_collection(coll_exercise)
        res_exercise = coll_exercises.delete_many(
            query_exercise
        )  # delete all exercises by userId

    if res_user.deleted_count >= 1:
        return {
            "user_delete_count": res_user.deleted_count,
            "exercises_delete_count": res_exercise.deleted_count,
        }
    else:
        return {"error": "userId not found"}


def update_user_claims(user, userId, option, newValue):

    updatedValue = newValue
    logger.info(f"update_user_claims")
    OPTION_CLAIMS = "user_claims"
    # Query user
    userInfo = get_user(user, userId)
    userClaims = []
    if "user_claims" in userInfo:
        for claims in userInfo["user_claims"]:
            userClaims.append(claims)

    try:
        query = {"_id": ObjectId(userId)}
    except Exception:
        return {"error": "Bad userId"}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_users,
        )
        if option == OPTION_CLAIMS:
            try:
                if updatedValue:
                    updatedValue = {
                        "user_claim_dates": datetime.datetime.strptime(
                            updatedValue["user_claim_dates"], "%Y-%m-%d %H:%M:%S.%f"
                        ),
                        "user_feedback": updatedValue["user_feedback"],
                    }
                    userClaims.append(updatedValue)
            except:
                return {"error": "claims data type incorrect"}
        res = coll.update(query, {"$set": {option: userClaims}}, False, True)
    logger.info(f"RES: {res}")
    if res["updatedExisting"]:
        return get_user(user, userId)
    else:
        return {"error": "userId not found"}


def update_user(user, userId, option, newValue):
    """Updates a User's information.

    Note:

    Args:
        user (str): Not required.
        userId (str): User Id.
        option (str): Field to update.
        newValue (str): Value to update option to.

    Returns:
        Dict containing the result updated.
    """
    updatedValue = newValue
    logger.info(f"update_user")

    OPTION_PASSWORD = "password"
    OPTION_USERNAME = "username"
    OPTION_PHONENO = "user_phone_no"
    OPTION_GENDER = "user_gender"
    OPTION_WEIGHT = "user_weight"
    OPTION_HEIGHT = "user_height"
    OPTION_AGE = "user_dob"
    OPTION_56KM_CHALLENGE = "56km_challenge"
    OPTION_USER_DISPLAY_NAME = "user_display_name"

    # Query user
    try:
        query = {"_id": ObjectId(userId)}
    except Exception:
        return {"error": "Bad userId"}
    if option == OPTION_PASSWORD:  # convert password to binary
        updatedValue = flask_bcrypt.generate_password_hash(updatedValue)

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_users,
        )
        if option == OPTION_USERNAME:
            filt = {"username": updatedValue}
            isExistingUsername = coll.find_one(filt)
            if isExistingUsername:
                return {"error": "username already exists"}
        elif option == OPTION_PHONENO:
            regex_pattern = re.compile("^[0-9]{8}$")
            isMatch = regex_pattern.match(updatedValue)
            if isMatch == None:
                return {"error": "phone number != formatted correctly"}
        elif option == OPTION_GENDER:
            if updatedValue not in gender_variables:
                return {"error": "gender != formatted correctly"}
        elif option == OPTION_HEIGHT:
            try:
                if updatedValue:
                    updatedValue = float(updatedValue)
            except:
                return {"error": "Height data type incorrect"}
        elif option == OPTION_AGE:
            try:
                if updatedValue:
                    updatedValue = datetime.datetime.strptime(
                        updatedValue, "%Y-%m-%d")
            except:
                return {"error": "Age data type incorrect"}
        elif option == OPTION_WEIGHT:
            try:
                if updatedValue:
                    updatedValue = float(updatedValue)
            except:
                return {"error": "Weight data type incorrect"}
        elif option == OPTION_56KM_CHALLENGE:
            try:
                if updatedValue:
                    updatedValue = datetime.datetime.strptime(
                        updatedValue, "%Y-%m-%d")
            except:
                return {"error": "56KM_CHALLENGE data type incorrect"}
        elif option == OPTION_USER_DISPLAY_NAME:
            # Check for profane user_display_name/
            if utils.is_profane(updatedValue):
                return {"error": "Bad Display Name"}
            dispatch_leaderboard_computation(
                user_id=userId, update_user_info_only=True)
        res = coll.update(query, {"$set": {option: updatedValue}}, False, True)
    logger.info(f"RES: {res}")
    if res["updatedExisting"]:
        return get_user(user, userId)
    else:
        return {"error": "userId not found"}


def get_user_exercises(
    user, userId, location="", start_date=0, end_date=0, reverse=True
):
    logger.info(f"get_user_exercises")
    if start_date < 0 or end_date < 0:
        return {"error": "Bad request, Invalid date input"}
    if start_date > end_date and end_date > 0:
        return {"error": "Bad request, Invalid date range"}

    # TODO: Check authorization

    # TODO: Should match userId to userId in database
    # Query user
    queryParams = []
    queryParams.append({"user_id": userId})
    if location != "":
        queryParams.append({"exercise_location": location})
    if start_date != 0:
        queryParams.append(
            {
                "exercise_ended": {
                    "$gte": milliseconds_since_epoch_to_datetime(start_date)
                }
            }
        )
    if end_date != 0:
        queryParams.append(
            {"exercise_ended": {
                "$lt": milliseconds_since_epoch_to_datetime(end_date)}}
        )

    query = {"$match": {"$and": queryParams}}

    # Projection
    proj = {
        "$project": {
            "_id": 0,
            "user_display_name": 1,
            # 'user_display_name': '$user_nickname',
            "user_gender": 1,
            "exercise_id": {"$toString": "$_id"},
            "exercise_name": 1,
            "exercise_location": 1,
            "exercise_started": 1,
            "exercise_ended": 1,
            "exercise_type": 1,
            "exercise_summary": 1,
        }
    }

    # Set sort order

    mongo_sort = pymongo.DESCENDING
    if reverse == False:
        mongo_sort = pymongo.ASCENDING
    # Sort
    sort = {"$sort": {"exercise_started": mongo_sort}}

    # Pipeline
    pipeline = [query, proj, sort]

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_exercise, codec_options=options)
        cur = coll.aggregate(pipeline)

    # Convert cursor to list
    cur_list = list(cur)

    if cur_list:
        return {"res": cur_list}
    else:
        return {"error": "Not found"}


def get_user_exercise_detail(user, userId, exerciseId):
    logger.info("get_user_exercise_detail")

    # TODO: Check authorization

    # Query user
    try:
        query = {
            "$match": {
                "$and": [
                    {"_id": ObjectId(exerciseId)},
                    {"user_id": userId},
                    # { 'user_nickname': userId },
                ]
            }
        }
    except Exception:
        return {"error": "Bad exercise id"}

    # Projection
    proj = {
        "$project": {
            "_id": 0,
            "user_display_name": 1,
            "user_gender": 1,
            "exercise_id": {"$toString": "$_id"},
            "exercise_name": 1,
            "exercise_location": 1,
            "exercise_started": 1,
            "exercise_ended": 1,
            "exercise_type": 1,
            "exercise_summary": 1,
            "exercise_data": 1,
            "created": 1,
        }
    }

    # Pipeline
    pipeline = [query, proj]

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_exercise,
            # codec_options=options
        )
        cur = coll.aggregate(pipeline)

    # Convert cursor to list
    cur_list = list(cur)
    if cur_list:
        return cur_list[0]  # Return the first and only result
    else:
        return {"error": "not found"}  # Return empty Dict


def register(user_data):
    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_users,
            # codec_options=options
        )

        filt = {"username": user_data["data"]["username"]}
        db_user = coll.find_one(filt)
        # if username existed in db return
        if not db_user:
            updt = {
                "$set": {
                    "password": flask_bcrypt.generate_password_hash(
                        user_data["data"]["password"]
                    ),
                    "user_display_name": user_data["data"]["displayname"],
                    "user_gender": user_data["data"]["gender"],
                    "user_phone_no": user_data["data"]["phonenumber"],
                    "user_registered": datetime.datetime.now(tz=tz_utc),
                }
            }

            result = coll.update_one(filt, updt, upsert=True)

            # TODO: Implement proper session key
            if result.upserted_id:
                response_body = {
                    # can consider uuid
                    "user_id": str(result.upserted_id),
                    "username": user_data["data"]["username"],
                    "user_phone_no": user_data["data"]["phonenumber"],
                }
            else:
                response_body = {}

            return response_body
        else:
            return False


def registerWithActiveSgQR(user_data):
    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_users,
            # codec_options=options
        )

        filt = {"activeSgId": user_data["data"]["activeSgId"]}
        db_user = coll.find_one(filt)
        # if username existed in db return
        cipher_phone_number = encrypt(user_data["data"]["phoneNo"])
        if not db_user:
            updt = {
                "$set": {
                    "user_phone_no": cipher_phone_number,
                    "user_display_name": utils.gen_random_user_display_name(),
                    "user_gender": "Male",
                    "username": "user1",
                    "user_registered": datetime.datetime.now(tz_utc),
                    "registered_date": {
                        "location": user_data["data"]["location"],
                        "device": user_data["data"]["device"],
                        "machineUUID": user_data["data"]["machineUUID"],
                        "time": datetime.datetime.now(tz_utc),
                    },
                }
            }

            result = coll.update_one(filt, updt, upsert=True)

            # TODO: Implement proper session key
            if result.upserted_id:
                response_body = {
                    # can consider uuid
                    "user_id": str(result.upserted_id),
                    "activeSgId": user_data["data"]["activeSgId"],
                    "username": "user1",
                }
                # publish to stage-3 trigger
                payload = dumps(response_body)
                numof_subs = r.publish(create_user_channel, payload)

            else:
                response_body = {}

            return response_body
        else:
            return False


def reset_username(user_id):
    query = {"_id": ObjectId(user_id)}

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_users,
            # codec_options=options
        )
    updt = {
        "$set": {
            "user_display_name": utils.gen_random_user_display_name(),
        },
    }
    res = coll.update_one(
        query,
        updt,
        upsert=True
    )
    dispatch_leaderboard_computation(
        user_id=user_id, update_user_info_only=True)
    return res


def login(username, password):
    # Query user
    query = {"username": username}
    proj = {"password"}

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_users,
            # codec_options=options
        )
    db_user = coll.find_one(query, proj)
    # logger.info(f'user {db_user}')

    try:
        isSuccess = flask_bcrypt.check_password_hash(
            db_user["password"], password)
        if db_user and isSuccess:
            logger.info("Login Passed!")
            # Rename field `_id` to `user_id` and convert to str
            db_user["user_id"] = str(db_user.pop("_id"))
            return db_user
        else:
            return False
    except ValueError as e:
        return False


def loginWithActiveSgQR(activeSgId):
    # Query user
    query = {"activeSgId": activeSgId}

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_users,
            # codec_options=options
        )
    db_user = coll.find_one(query)
    # logger.info(f'user {db_user}')
    # print(f'user {db_user}')

    try:
        if db_user:
            logger.info("Login Passed!")
            # Rename field `_id` to `user_id` and convert to str
            db_user["user_id"] = str(db_user.pop("_id"))
            return db_user
        else:
            return False
    except ValueError as e:
        return False


def logout(userid):
    """Deletes access and refresh tokens

    Args:
      userid: UserId to log out
    Return:
      True if succeed, False otherwise
    """

    logger.debug(f"logout")

    # Access token
    doc = {"sub": userid}
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_accesstokens)

    try:
        coll.delete_many(doc)
    except Exception as e:
        logger.error(e)
        return False

    return True


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


def dispatch_machine(user: str, machineId: str) -> str:
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


def dispatch_weightstack(payloadData):
    logger.debug("dispatch_weightstack start")
    machineId = payloadData["machineId"]
    payloadData = json.dumps(payloadData)

    revert = bool(os.getenv('REVERT_STAGE1', False))
    if revert:
        numof_subs = r.publish(channel_weightstack, payloadData)
        msg = f"Dispatched weightstack streaming {machineId} to {numof_subs} subscribers"
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


def dispatch_bodyweight(machineId, payloadData):
    logger.debug("dispatch_bodyweight start")

    payloadData = json.dumps(payloadData)

    revert = bool(os.getenv('REVERT_STAGE1', False))
    if revert:
        numof_subs = r.publish(channel_bodyweight, payloadData)
        msg = f"Dispatched bodyweight {machineId} to {numof_subs} subscribers"
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


def dispatch_weighingscale(machineId):

    logger.debug("dispatch_weighingscale start")

    payloadData = machineId

    revert = bool(os.getenv('REVERT_STAGE1', False))
    if revert:
        numof_subs = r.publish(channel_weighingscale, payloadData)
        msg = f"Dispatched weighing scale {machineId} to {numof_subs} subscribers"
    else:
        payloadData = {"machineId": machineId}
        payloadData = json.dumps(payloadData)
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


def dispatch_bike_worker(machineId):

    logger.debug("dispatch_bike_worker start")

    payloadData = {"machineId": machineId}
    payloadData = json.dumps(payloadData)

    revert = bool(os.getenv('REVERT_STAGE1', False))
    if revert:
        numof_subs = r.publish(channel_bike, payloadData)
        msg = f"Dispatched bike worker {machineId} to {numof_subs} subscribers"
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


def dispatch_campaign_calculation(user_id, location, target):

    logger.debug(f"dispatch_campaign_calculation start: {location}")

    payload_data = {
        "user_id": user_id,
        "location": location,
        "target": target,
        "type": "campaign-computation"
    }
    payload_data = json.dumps(payload_data)

    revert = bool(os.getenv('REVERT_STAGE3', False))
    if revert:
        numof_subs = r.publish(channel_campaign_calculation, payload_data)
        msg = f"Dispatched campaign calculation for {user_id} in {location} to {numof_subs} subscribers"
    else:
        with RMQ(rabbitmq_ip, rabbitmq_port, rabbitmq_user, rabbitmq_pw) as conn:
            channel = conn.channel()
            # channel.queue_delete(queue=queue)
            channel.queue_declare(
                queue=rabbitmq_processing_queue, durable=True)
            channel.basic_publish(exchange='',
                                  routing_key=rabbitmq_processing_queue,
                                  body=payload_data,
                                  properties=pika.BasicProperties(
                                      delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
                                  )
            msg = f"Dispatched campaign calculation to {rabbitmq_processing_queue} rabbitmq queue"

    logger.info(msg)
    return msg


def dispatch_bpm(machineId):

    # Old dispatch code
    #
    # logger.debug("dispatch_bpm start")

    # payload_data = machineId
    # numof_subs = r.publish(channel_bpm, payload_data)

    # msg = f"Dispatched bpm {machineId} to {numof_subs} subscribers"
    # # logger.info(msg)

    # return msg

    # new dispatch code

    logger.debug("dispatch_bpm start")

    payloadData = machineId

    revert = bool(os.getenv('REVERT_STAGE1', False))
    if revert:
        numof_subs = r.publish(channel_bpm, payloadData)
        msg = f"Dispatched bpm {machineId} to {numof_subs} subscribers"
    else:
        payloadData = {"machineId": machineId}
        payloadData = json.dumps(payloadData)
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


def bulk_get_availability():
    """Handler for /machines/bulk_get_availability

    Args:
      Nothing
    Returns:
      List of Dict with keys 'machineId' and 'availability'
    """

    logger.debug(f"Step into bulk_get_availability()")

    pattern = "*:available"
    keys = r.keys(pattern)

    result = []
    for k in range(len(keys)):
        machineId = keys[k].decode().split(":")[0]
        available = r.get(keys[k])
        locationByte = (
            r.get(str.encode(machineId + ":location")) or b"no-location"
        )  # null checkers
        location = locationByte.decode()
        machineTypeByte = (
            r.get(str.encode(machineId + ":type")) or b"no-type"
        )  # null checkers
        machineTypeStr = machineTypeByte.decode()
        muscleGroupByte = (
            r.get(str.encode(machineId + ":muscle_group")) or b"no-muscle-group"
        )
        muscleGroupStr = muscleGroupByte.decode()
        try:
            result.append(
                {
                    "machineId": machineId,
                    "availability": bool(int(available)),
                    "location": location,
                    "type": machineTypeStr,
                    "muscleType": muscleGroupStr,
                }
            )
        except Exception:
            pass

    return result


def bulk_set_availability(body: list):
    """Handler for /machines/bulk_set_availability

    Args:
      body: List of Dict with keys 'machineId' and 'availability'
    Returns:
      Nothing
    """

    logger.debug(f"Step into bulk_set_availability()")

    # Iterate over list
    # Expects { 'machineId': string, 'availability': boolean }
    for ele in body:
        machineId = ele["machineId"]
        key = f"{machineId}:available"
        if ele["availability"]:
            r.set(key, 1)
            logger.info(f"Set :available to 1")
        else:
            r.set(key, 0)
            logger.info(f"Set :available to 0")

    return {}


def validate_api_key(apikey: str):
    query = {"apikey": apikey}
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_apikeys)
        res = coll.find_one(query)

    if res:
        return res["account"]
    else:
        return None


def create_service_account(body):
    doc = {
        "apikey": secrets.token_urlsafe(16),
        "account": f"sgymsvcs${body['account_name']}",
        "created": datetime.datetime.now(tz=tz_utc),
    }

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_apikeys)
        result = coll.insert_one(doc)

    if result.acknowledged:
        doc.pop("_id")
        doc.pop("created")
        return doc
    else:
        return None


def delete_service_account(accountName):
    query = {
        "account": f"sgymsvcs${accountName}",
    }

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_apikeys,
        )
        res = coll.delete_one(query)

    if res.deleted_count >= 1:
        return {"deleted count": res.deleted_count}
    else:
        return {"error": "Not found"}


# TODO: Remove X_10MBCLevel9?
def dispatch_leaderboard_computation(
    user_id: str = "",
    location: list = [
        "ActiveSG@HBB",
        "ActiveSG@JE",
        "ActiveSG@OTH",
        "10MBCLevel9",
        "X_10MBCLevel9",
    ],
    update_user_info_only: bool = False,
    recalculate_leaderboard: bool = False,
):
    """Dispatches Dict containing user_id and location to a leaderboard-computation channel in Redis.
    Args:
        user_id (str)
        location (str)
    Returns:
        None
    """

    payload_data = {
        "user_id": user_id,
        "location": location,
        "user_info_update": update_user_info_only,
        "recalculate_leaderboard":recalculate_leaderboard,
        "type": "leaderboard-computation"
    }

    payload_data2 = {
        "user_id": user_id,
        "location": location,
        "user_info_update": update_user_info_only,
        "recalculate_leaderboard":recalculate_leaderboard,
        "type": "fastest-run-computation"
    }
    payload_data = json.dumps(payload_data)
    payload_data2 = json.dumps(payload_data2)
    revert = bool(os.getenv('REVERT_STAGE3', False))
    if revert:
        num_of_subs = r.publish("leaderboard-computation", payload_data)
        msg = f"Dispatched leaderboard calculation for {user_id} in {location} to {num_of_subs} subscribers."
    else:
        with RMQ(rabbitmq_ip, rabbitmq_port, rabbitmq_user, rabbitmq_pw) as conn:
            channel = conn.channel()
            # channel.queue_delete(queue=queue)
            channel.queue_declare(
                queue=rabbitmq_processing_queue, durable=True)
            channel.basic_publish(exchange='',
                                  routing_key=rabbitmq_processing_queue,
                                  body=payload_data,
                                  properties=pika.BasicProperties(
                                      delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
                                  )
            channel.basic_publish(exchange='',
                                routing_key=rabbitmq_processing_queue,
                                body=payload_data2,
                                properties=pika.BasicProperties(
                                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
                                )
            msg = f"Dispatched leaderboard calculation to {rabbitmq_processing_queue} rabbitmq queue"

    logger.info(msg)
    return msg


def get_monthly_leaderboard(limit: int, location: str, metric: str, age_lower: int, age_upper: int, gender: str, desc:bool):
    """Fetches a current-month intra-gym leaderboard.
    Args:
      limit: int
      location: str
      metric: str

    Returns:
      List of dictionaries containing [score], [user_display_name] and [user_id]
    """

    # Get scores by userId
    data = r.zrange(
        f"leaderboard:intraGym:{location}:{metric}",
        0,
        limit - 1,
        desc=desc,
        withscores=True,
    )

    # Make Schema.
    ret = []
    for user_id, score in data:
        user_id = user_id.decode()
        user_info = dict(json.loads(r.hget("leaderboard:intraGym:userInfo", user_id)))

        if not isinstance(user_info["user_age"], int):
            user_info["user_age"] = -1

        if (age_lower != 0 or age_upper != 100) and (user_info["user_age"] < age_lower or user_info["user_age"] > age_upper):
            continue
        if gender != "" and user_info["user_gender"] != gender:
            continue

        ret.append(dict( **user_info, **
                   {"score": score, "user_id": user_id}))

    
    # return "test"
    return ret


def get_user_metrics_by_dates_gyms(
    user_id: str,
    start_date: str = "2020-01-01",
    end_date: str = None,
    gyms=["ActiveSG@HBB", "ActiveSG@JE", "ActiveSG@OTH", "10MBCLevel9"],
):
    """Calculates a metrics for a user across gyms and a date range.
    Args:
        metric (str): Leaderboard Metric
        start_date (datetime Obj): Defaults to 2020-01-01.
        end_date (datetime Obj): Defaults to today's date - UTC.
        gyms (list[str]): Defaults to all gyms.

    Returns:
        Dict containing [user_id], [score] and [user_display_name].
    """

    # Parse Inputs
    if end_date is None:
        end_date = datetime.datetime.today()
    else:
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")

    # Pipeline

    user_filter = {
        "$match": {
            "user_id": user_id,
        }
    }

    date_filter = {
        "$match": {
            "created": {
                "$gte": start_date,
                "$lte": end_date,
            },
        }
    }

    gyms_filter = {"$match": {"$expr": {"$in": ["$exercise_location", gyms]}}}

    add_fields = {
        "$addFields": {
            "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created"}},
            "user_obj_id": {"$toObjectId": "$user_id"},
        }
    }

    calc_metrics = {
        # Group
        "$group": {
            "_id": {
                "user": "$user_obj_id",
            },
            # Calculate active-minutes
            "active-minutes": {
                "$sum": {
                    "$divide": [
                        {"$subtract": ["$exercise_ended",
                                       "$exercise_started"]},
                        60000,
                    ]
                }
            },
            # Calculate calories-burnt
            "calories-burnt": {"$sum": "$exercise_summary.calories"},
            # Calculate weight-lifted
            "weight-lifted": {
                "$sum": {
                    "$cond": {
                        "if": {
                            "$in": [
                                "$exercise_type",
                                ["chestpress", "weightstack", "abdominal"],
                            ]
                        },
                        "then": {
                            "$multiply": [
                                "$exercise_summary.reps",
                                "$exercise_summary.weight",
                            ]
                        },
                        "else": 0,
                    }
                }
            },
            # Calculate cardio-minutes
            "cardio-minutes": {
                "$sum": {
                    "$cond": {
                        "if": {"$in": ["$exercise_type", ["treadmill", "bike"]]},
                        "then": {
                            "$divide": [
                                {
                                    "$subtract": [
                                        "$exercise_ended",
                                        "$exercise_started",
                                    ]
                                },
                                60000,
                            ]
                        },
                        "else": 0,
                    }
                }
            },
            # Fetch unique gym-days
            "gym-attendance": {
                "$addToSet": "$day",
            },
            # Calculate distance-run
            "distance-run": {
                "$sum": {
                    "$cond": {
                        "if": {"$in": ["$exercise_type", ["treadmill"]]},
                        "then": {"$divide": ["$exercise_summary.total_distance", 1000]},
                        "else": 0,
                    }
                }
            },
        },
    }

    user_params = {
        "$lookup": {
            "from": "users",
            "localField": "_id.user",
            "foreignField": "_id",
            "as": "user_params",
        }
    }

    remove_empty_user_params = {
        "$match": {
            "user_params": {"$ne": []},
        }
    }

    project_output = {
        "$project": {
            # User Details
            "user_display_name": {
                "$arrayElemAt": ["$user_params.user_display_name", 0]
            },
            # Leaderboard Metrics
            "weight-lifted": 1,
            "calories-burnt": 1,
            "cardio-minutes": 1,
            "active-minutes": 1,
            "gym-attendance": {"$size": "$gym-attendance"},
            "distance-run": 1,
            # Remove
            "_id": 0,
        }
    }

    pipeline = [
        user_filter,
        date_filter,
        gyms_filter,
        add_fields,
        calc_metrics,
        user_params,
        remove_empty_user_params,
        project_output,
    ]

    # Apply
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_exercise)
        cur = coll.aggregate(pipeline)

    # Result
    res = list(cur)

    if res:
        return res[0]
    else:
        return None


def get_leaderboard_by_dates_gyms(
    metric: str,
    limit: int,
    start_date: str = "2020-01-01",
    end_date: str = None,
    gyms=["ActiveSG@HBB", "ActiveSG@JE", "ActiveSG@OTH", "10MBCLevel9"],
):
    """Returns an on demand leaderboard.

    Args:
        metric (str): Leaderboard Metric
        start_date (datetime Obj): Defaults to 2020-01-01.
        end_date (datetime Obj): Defaults to today's date - UTC.
        gyms (list[str]): Defaults to all gyms.
        limit (int): Number to limit response by.

    Returns:
        list[dict] containing [user_phone_no], [score] and [user_display_name].
    """

    # Parse Inputs
    if end_date is None:
        end_date = datetime.datetime.today()
    else:
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")

    # Pipeline
    date_filter = {
        "$match": {
            "created": {
                "$gte": start_date,
                "$lte": end_date,
            },
        }
    }

    gyms_filter = {"$match": {"$expr": {"$in": ["$exercise_location", gyms]}}}

    add_fields = {
        "$addFields": {
            "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created"}},
            "user_obj_id": {"$toObjectId": "$user_id"},
        }
    }

    calc_metric = _leaderboard_metric_calculation_stage(metric=metric)

    user_params = {
        "$lookup": {
            "from": "users",
            "localField": "_id.user",
            "foreignField": "_id",
            "as": "user_params",
        }
    }

    remove_empty_user_params = {
        "$match": {
            "user_params": {"$ne": []},
        }
    }

    project_output = {
        "$project": {
            # User Details
            "user_display_name": {
                "$arrayElemAt": ["$user_params.user_display_name", 0]
            },
            "user_id": {"$toString": "$_id.user"},
            # Leaderboard Metrics
            "gym": "$_id.gym",
            metric: 1 if metric != "gym-attendance" else {"$size": "$gym-attendance"},
            # Remove
            "_id": 0,
        }
    }

    sort_output = {
        "$sort": {
            metric: -1,
        }
    }

    limit_output = {
        "$limit": limit,
    }

    pipeline = [
        date_filter,
        gyms_filter,
        add_fields,
        calc_metric,
        user_params,
        remove_empty_user_params,
        project_output,
        sort_output,
        limit_output,
    ]

    # Apply
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_exercise)
        cur = coll.aggregate(pipeline)

    return _leaderboard_filter_invalid_results(cur, metric=metric)


def _leaderboard_metric_calculation_stage(metric):
    """Returns a relevant metric calculation pipeline stage.

    Args:
        metric (str): Metric to calculate.

    Returns:
        calc_metric (dict): MongoDB metric calculation pipeline stage.
    """

    # Group by user.
    calc_metric = {
        "$group": {
            "_id": {
                "user": "$user_obj_id",
            }
        }
    }

    # Add metric calculation phase.
    if metric == "active-minutes":
        calc_metric["$group"][metric] = {
            "$sum": {
                "$divide": [
                    {"$subtract": ["$exercise_ended", "$exercise_started"]},
                    60000,
                ]
            }
        }
    elif metric == "weight-lifted":
        calc_metric["$group"][metric] = {
            "$sum": {
                "$cond": {
                    "if": {
                        "$in": [
                            "$exercise_type",
                            ["chestpress", "weightstack", "abdominal"],
                        ]
                    },
                    "then": {
                        "$multiply": [
                            "$exercise_summary.reps",
                            "$exercise_summary.weight",
                        ]
                    },
                    "else": 0,
                }
            }
        }
    elif metric == "cardio-minutes":
        calc_metric["$group"][metric] = {
            "$sum": {
                "$cond": {
                    "if": {"$in": ["$exercise_type", ["treadmill", "bike"]]},
                    "then": {
                        "$divide": [
                            {
                                "$subtract": [
                                    "$exercise_ended",
                                    "$exercise_started",
                                ]
                            },
                            60000,
                        ]
                    },
                    "else": 0,
                },
            }
        }
    elif metric == "calories-burnt":
        calc_metric["$group"][metric] = {"$sum": "$exercise_summary.calories"}
    elif metric == "active-minutes":
        calc_metric["$group"][metric] = {
            "$sum": {
                "$divide": [
                    {"$subtract": ["$exercise_ended", "$exercise_started"]},
                    60000,
                ]
            }
        }
    elif metric == "gym-attendance":
        calc_metric["$group"][metric] = {
            "$addToSet": "$day",
        }
    elif metric == "distance-run":
        calc_metric["$group"][metric] = {
            "$sum": {
                "$cond": {
                    "if": {"$in": ["$exercise_type", ["treadmill"]]},
                    "then": {"$divide": ["$exercise_summary.total_distance", 1000]},
                    "else": 0,
                }
            }
        }
    else:
        raise Exception("Metric is not defined!")
    return calc_metric


def _leaderboard_filter_invalid_results(cur, metric):
    """Masks phone no., removes invalid UserIds and user_display_names, and sets NaNs to 0s.
    Args:
        cur (list[dict]): Contains [leaderboard-metric], [gym], [user_display_name], [user_id], and [user_phone_no].
        metric (str): Leaderboard Metric.
        limit (int): Number to limit response by.

    Returns:
        list[dict] that contain [leaderboard-metric], [gym], [user_display_name], [user_id], and [user_phone_no].
    """

    cur = list(cur)

    # Clean
    for result in cur:
        # Nan protection
        if math.isnan(result[metric]):
            result[metric] = 0
        # Score/Metric Name Change
        result["score"] = result.pop(metric)

    # Remove 0s.
    return [result for result in cur if result["score"] != 0]


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

    return out


def ban_leaderboard_user(user_id: str):
    r.sadd("leaderboard:blacklist", user_id)
    dispatch_leaderboard_computation(user_id=user_id)
    return user_id


def ban_leaderboard_user_mongo(user_id: str, location: str):
    # function to add banned user in mongo here
    query = {"user_id": user_id}
    dt_start_ban = datetime.datetime.now(tz_utc)
    dt_start_ban_ep = dt_start_ban.timestamp() * 1000
    dt_end_ban = dt_start_ban + datetime.timedelta(days=30)
    dt_end_ban_ep = dt_end_ban.timestamp() * 1000
    body = {
        "user_id": user_id,
        "start_ban": dt_start_ban,
        "end_ban": dt_end_ban,
        "ban_issued_by": location
    }

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_ban_users)
        res = coll.update_one(query, {"$set": body}, upsert=True)

    dispatch_leaderboard_computation(user_id=user_id)
    return user_id


def fetch_banned_leaderboard_users_mongo(location: str):
    query_params = []
    query_params.append({"start_ban": {"$lt": datetime.datetime.now(tz_utc)}})
    query_params.append({"end_ban": {"$gt": datetime.datetime.now(tz_utc)}})

    if location.lower() != "all":
        query_params.append({"ban_issued_by": location})

    query = {"$match": {"$and": query_params}}

    projection = {
        "$project": {
            "_id": 0,
            "user_id": 1,
            "start_ban": 1,
            "end_ban": 1,
            "ban_issued_by": 1
        }
    }
    pipeline = [query, projection]

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_ban_users)
        res = list(coll.aggregate(pipeline))

    return_res = []

    for i in range(len(res)):
        temp_res = get_user(None, userId=res[i]["user_id"])

        if "user_display_name" in temp_res:
            res[i].update({"user_display_name": temp_res["user_display_name"]})
            return_res.append(res[i])

    return {"result": return_res}


def unban_leaderboard_user_mongo(user_id: str):
    query = {"user_id": user_id}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_ban_users)
        res = coll.delete_one(query)

    dispatch_leaderboard_computation(user_id=user_id)
    return user_id


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


def is_refresh_token_good(token):
    """Check if refresh token is still in database

    Args:
      token: Query token
    Return:
      bool: True if still in database, False otherwise
    """

    # Convert timestamp
    token = timestamp2datetime(token)

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_refreshtokens)
        result = coll.find_one(token)
        logger.debug(f"find_one result")

    if result:
        return True
    else:
        return False


def is_access_token_good(token):
    """Check if access token is still in database

    Args:
      token: Query token
    Return:
      bool: True if still in database, False otherwise
    """

    # Convert timestamp
    token = timestamp2datetime(token)

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_accesstokens)
        result = coll.find_one(token)
        logger.debug(f"find_one result")

    if result:
        return True
    else:
        return False


def insert_refresh_token(doc):
    """Insert a refresh token into the refreshtokens collection

    Args:
      doc: Token to insert
    Return:
      Nothing
    """

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_refreshtokens)
        result = coll.insert_one(doc)


def timestamp2datetime(jwt):
    """Converts jwt time fields from timestamp to datetime

    Args:
      jwt: JWT
    Returns:
      JWT token with datetime fields
    """

    jwt["iat"] = datetime.datetime.fromtimestamp(jwt["iat"])
    jwt["exp"] = datetime.datetime.fromtimestamp(jwt["exp"])

    return jwt


def refresh_tokens(new_access_token, new_refresh_token):
    """Deletes old access and refresh tokens and
    inserts new access and refresh tokens

    Args:
      new_access_token: New access token
      new_refresh_token: New refresh token
    Return:
      Nothing
    """

    # logger.debug(new_access_token)
    # logger.debug(new_refresh_token)

    # Get user_id
    user_id = new_access_token["sub"]

    # Access token
    doc = {"sub": user_id}
    token = timestamp2datetime(new_access_token)
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_accesstokens)

    try:
        coll.delete_many(doc)
        coll.insert_one(token)
    except Exception as e:
        logger.error(e)

    # Refresh token
    doc = {"sub": user_id}
    token = timestamp2datetime(new_refresh_token)
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_refreshtokens)

    try:
        coll.delete_many(doc)
        coll.insert_one(token)
    except Exception as e:
        logger.error(e)


def calculateUserCampaignStatus(user, userid):

    campaignLevels = {
        "levelOneTreadmill": 600,
        "levelOneWeightStack": 20,
        "levelTwoTreadmill": 900,
        "levelTwoWeightStack": 30,
        "levelThreeTreadmill": 1200,
        "levelThreeWeightStack": 40,
    }

    tempStatus = -1
    tempExerciseDate = None

    campaignStartDate = datetime.datetime(2021, 1, 18).astimezone(tz_utc)
    campaignEndDate = datetime.datetime(2021, 4, 1).astimezone(tz_utc)
    todayDate = datetime.datetime.today().astimezone(tz_utc)
    print("dates: ", [campaignStartDate, campaignEndDate, todayDate])

    userInfo = get_user(user, userid)
    # print("userInfo: ", userInfo)
    userExercises = get_user_exercises(user, userid, False)
    # print("userExercises: ", userExercises)

    bodyMetrics = mongoGetBodyMetricsList(userid, sort_date_by="ASC", limit=0)
    # print("bodyMetrics: ", bodyMetrics)

    for elem in bodyMetrics:
        elem["created"] = elem["created"].strftime("%Y-%m-%dT%H:%M:%SZ")

    tempPreviousExercisesDate = None
    tempLevelTreadmill = 0
    tempLevelWeightStack = 0

    user_campaign_status = []
    for bodyMetricsResults in bodyMetrics:

        # print('break')
        # print(bodyMetricsResults['created'])
        bodyMetricsResultsDatetime = datetime.datetime.strptime(
            bodyMetricsResults["created"], "%Y-%m-%dT%H:%M:%SZ"
        )
        bodyMetricsResultsDate = datetime.datetime(
            bodyMetricsResultsDatetime.year,
            bodyMetricsResultsDatetime.month,
            bodyMetricsResultsDatetime.day,
        ).astimezone(tz_utc)
        # print("bodyMetricsResultsDate: ",bodyMetricsResultsDate)
        # print("sgCampaignStartDate: ",sgCampaignStartDate)
        # print("sgCampaignEndDate: ",sgCampaignEndDate)
        # print(bodyMetricsResultsDate >= sgCampaignStartDate)
        # print(bodyMetricsResultsDate <= sgCampaignEndDate)
        if (
            bodyMetricsResultsDate >= campaignStartDate
            and bodyMetricsResultsDate <= campaignEndDate
        ):
            tempStatus += 1
            user_campaign_status.append(
                {
                    "bodymetrics_date": datetime.datetime.combine(
                        bodyMetricsResultsDate, datetime.datetime.min.time()
                    ),
                }
            )
            # print('campaign started')
            # print(tempStatus)
            tempWeightingScaleDate = bodyMetricsResultsDate
            for userExercisesResults in userExercises:

                if tempStatus == 4 or tempStatus == 11 or tempStatus == 20:
                    # print("enter weightscale checking -----------")
                    for bodyMetricsResults2 in bodyMetrics:
                        bodyMetricsResultsDatetime2 = datetime.datetime.strptime(
                            bodyMetricsResults2["created"], "%Y-%m-%dT%H:%M:%SZ"
                        )
                        tempWeightingScaleDate = datetime.datetime(
                            bodyMetricsResultsDatetime2.year,
                            bodyMetricsResultsDatetime2.month,
                            bodyMetricsResultsDatetime2.day,
                        ).astimezone(tz_utc)
                        # print(tempWeightingScaleDate)
                        # print(tempPreviousExercisesDate)
                        # print(tempWeightingScaleDate >=
                        #       tempPreviousExercisesDate)
                        if (
                            tempWeightingScaleDate
                            >= (tempPreviousExercisesDate - datetime.timedelta(days=1))
                            and tempWeightingScaleDate <= campaignEndDate
                        ):
                            tempStatus += 1
                            user_campaign_status.append(
                                {
                                    "bodymetrics_date": datetime.datetime.combine(
                                        tempWeightingScaleDate,
                                        datetime.datetime.min.time(),
                                    ),
                                }
                            )
                            break

                # print('tracking exercise for campaign')
                # print([tempLevelTreadmill, tempLevelWeightStack])
                checkTempExerciseDate = datetime.datetime(
                    userExercisesResults["exercise_started"].year,
                    userExercisesResults["exercise_started"].month,
                    userExercisesResults["exercise_started"].day,
                ).astimezone(tz_utc)
                if checkTempExerciseDate > campaignEndDate:
                    break
                tempExerciseDate = datetime.datetime(
                    userExercisesResults["exercise_started"].year,
                    userExercisesResults["exercise_started"].month,
                    userExercisesResults["exercise_started"].day,
                ).astimezone(tz_utc)
                if (
                    (
                        tempPreviousExercisesDate == None
                        or tempPreviousExercisesDate != tempExerciseDate
                    )
                    and tempStatus <= 21
                    and tempStatus > 11
                ):
                    # print("level three checking -------------")
                    if (
                        tempLevelTreadmill >= campaignLevels["levelThreeTreadmill"]
                        and tempLevelWeightStack
                        >= campaignLevels["levelThreeWeightStack"]
                    ):
                        tempStatus += 1
                        user_campaign_status.append(
                            {
                                "exercise_date": datetime.datetime.combine(
                                    tempPreviousExercisesDate,
                                    datetime.datetime.min.time(),
                                ),
                            }
                        )
                    tempPreviousExercisesDate = tempExerciseDate
                    tempLevelTreadmill = 0
                    tempLevelWeightStack = 0
                if (
                    (
                        tempPreviousExercisesDate == None
                        or tempPreviousExercisesDate != tempExerciseDate
                    )
                    and tempStatus <= 12
                    and tempStatus > 4
                ):
                    # print("level two checking -------------")
                    if (
                        tempLevelTreadmill >= campaignLevels["levelTwoTreadmill"]
                        and tempLevelWeightStack
                        >= campaignLevels["levelTwoWeightStack"]
                    ):
                        tempStatus += 1
                        user_campaign_status.append(
                            {
                                "exercise_date": datetime.datetime.combine(
                                    tempPreviousExercisesDate,
                                    datetime.datetime.min.time(),
                                ),
                            }
                        )
                    tempPreviousExercisesDate = tempExerciseDate
                    tempLevelTreadmill = 0
                    tempLevelWeightStack = 0
                if (
                    tempPreviousExercisesDate == None
                    or tempPreviousExercisesDate != tempExerciseDate
                ) and tempStatus < 4:
                    # print("level one checking -------------")
                    if (
                        tempLevelTreadmill >= campaignLevels["levelOneTreadmill"]
                        and tempLevelWeightStack
                        >= campaignLevels["levelOneWeightStack"]
                    ):
                        tempStatus += 1
                        user_campaign_status.append(
                            {
                                "exercise_date": datetime.datetime.combine(
                                    tempPreviousExercisesDate,
                                    datetime.datetime.min.time(),
                                ),
                            }
                        )
                    tempPreviousExercisesDate = tempExerciseDate
                    tempLevelTreadmill = 0
                    tempLevelWeightStack = 0

                if (
                    tempExerciseDate >= tempWeightingScaleDate
                    and tempExerciseDate <= campaignEndDate
                ):
                    if (
                        userExercisesResults["exercise_type"] == "chestpress"
                        or userExercisesResults["exercise_type"] == "weightstack"
                    ):
                        tempLevelWeightStack += userExercisesResults[
                            "exercise_summary"
                        ]["reps"]

                    if userExercisesResults["exercise_type"] == "treadmill":
                        tempLevelTreadmill += userExercisesResults["exercise_summary"][
                            "duration"
                        ]
            if tempStatus <= 21 and tempStatus > 11 and tempExerciseDate != None:
                # print("level three checking -------------")
                if (
                    tempLevelTreadmill >= campaignLevels["levelThreeTreadmill"]
                    and tempLevelWeightStack >= campaignLevels["levelThreeWeightStack"]
                ):
                    tempStatus += 1
                    user_campaign_status.append(
                        {
                            "exercise_date": datetime.datetime.combine(
                                tempPreviousExercisesDate, datetime.datetime.min.time()
                            ),
                        }
                    )
                tempPreviousExercisesDate = tempExerciseDate
                tempLevelTreadmill = 0
                tempLevelWeightStack = 0
            if tempStatus <= 12 and tempStatus > 4 and tempExerciseDate != None:
                # print("level two checking -------------")
                if (
                    tempLevelTreadmill >= campaignLevels["levelTwoTreadmill"]
                    and tempLevelWeightStack >= campaignLevels["levelTwoWeightStack"]
                ):
                    tempStatus += 1
                    user_campaign_status.append(
                        {
                            "exercise_date": datetime.datetime.combine(
                                tempPreviousExercisesDate, datetime.datetime.min.time()
                            ),
                        }
                    )
                tempPreviousExercisesDate = tempExerciseDate
                tempLevelTreadmill = 0
                tempLevelWeightStack = 0
            if tempStatus < 4 and tempExerciseDate != None:
                # print("level one checking -------------")
                if (
                    tempLevelTreadmill >= campaignLevels["levelOneTreadmill"]
                    and tempLevelWeightStack >= campaignLevels["levelOneWeightStack"]
                ):
                    tempStatus += 1
                    user_campaign_status.append(
                        {
                            "exercise_date": datetime.datetime.combine(
                                tempPreviousExercisesDate, datetime.datetime.min.time()
                            ),
                        }
                    )
                tempPreviousExercisesDate = tempExerciseDate
                tempLevelTreadmill = 0
                tempLevelWeightStack = 0

            if tempStatus == 4 or tempStatus == 11 or tempStatus == 20:
                # print("enter weightscale checking last -----------")
                for bodyMetricsResults2 in bodyMetrics:
                    bodyMetricsResultsDatetime2 = datetime.datetime.strptime(
                        bodyMetricsResults2["created"], "%Y-%m-%dT%H:%M:%SZ"
                    )
                    tempWeightingScaleDate = datetime.datetime(
                        bodyMetricsResultsDatetime2.year,
                        bodyMetricsResultsDatetime2.month,
                        bodyMetricsResultsDatetime2.day,
                    ).astimezone(tz_utc)
                    # print(tempWeightingScaleDate)
                    # print(tempPreviousExercisesDate)
                    # print(tempWeightingScaleDate >=
                    #       (tempPreviousExercisesDate))
                    if (
                        tempWeightingScaleDate >= (tempPreviousExercisesDate)
                        and tempWeightingScaleDate <= campaignEndDate
                    ):
                        tempStatus += 1
                        # print(tempStatus)
                        user_campaign_status.append(
                            {
                                "bodymetrics_date": datetime.datetime.combine(
                                    tempWeightingScaleDate, datetime.datetime.min.time()
                                ),
                            }
                        )
                        break
            if tempStatus > 21:
                tempStatus = 21
            if "user_claims" in userInfo:
                campaignStatusResult = {
                    "user_status": tempStatus,
                    "user_claims": len(userInfo["user_claims"]),
                }
            else:
                campaignStatusResult = {
                    "user_status": tempStatus, "user_claims": 0}
            update_user(user, userid, "user_campaign_status",
                        user_campaign_status)
            return campaignStatusResult
    if "user_claims" in userInfo:
        campaignStatusResult = {
            "user_status": tempStatus,
            "user_claims": len(userInfo["user_claims"]),
        }
    else:
        campaignStatusResult = {"user_status": tempStatus, "user_claims": 0}
    update_user(user, userid, "user_campaign_status", user_campaign_status)
    return campaignStatusResult


def get_campaigns(active):
    cur_time = datetime.datetime.now()
    if active is None:
        query = {}
    elif active is True:
        query = {
            "$and": [
                {"start_date": {"$lt": cur_time}},
                {"end_date": {"$gte": cur_time}},
            ]
        }
    else:
        query = {
            "$or": [{"start_date": {"$gte": cur_time}}, {"end_date": {"$lt": cur_time}}]
        }

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_campaigns,
        )
        res = coll.find(query)

    if res:
        collList = list(res)
        for elem in collList:
            elem["_id"] = str(elem["_id"])
        return {"res": collList}
    else:
        return {"error": "Not found"}


def get_campaign_by_id(campaignId: str):
    try:
        query = {"_id": ObjectId(campaignId)}
    except:
        return {"error": "Bad campaign id"}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_campaigns,
        )
        res = coll.find_one(query)

    if res:
        res["_id"] = str(res["_id"])
        return res
    else:
        return {"error": "Not found"}


def post_campaign(body):
    body = validate_datetime(body)
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_campaigns)
        queryLocation = {"location": body["location"]}
        dateRange = namedtuple("Range", ["start", "end"])
        campaignResult = coll.find(queryLocation)
        for x in campaignResult:
            r1 = dateRange(start=body["start_date"], end=body["end_date"])
            r2 = dateRange(start=x["start_date"], end=x["end_date"])
            latest_start = max(r1.start, r2.start)
            earliest_end = min(r1.end, r2.end)
            delta = (earliest_end - latest_start).days + 1
            overlap = max(0, delta)
            if overlap > 0:
                return {"error": "Campaign Duration Overlap"}
        result = coll.insert_one(body)

    return result.acknowledged


def delete_campaign(campaignId: str):
    try:
        query = {"_id": ObjectId(campaignId)}
    except:
        return {"error": "Bad campaign id"}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_campaigns,
        )
        res = coll.delete_one(query)

    if res.deleted_count >= 1:
        return {"deleted count": res.deleted_count}
    else:
        return {"error": "Not found"}


def get_user_campaign_status(campaignId: str, userId: str):
    try:
        query = {"$and": [{"campaign_id": campaignId}, {"user_id": userId}]}
    except:
        return {"error": "Bad campaign id or user id"}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_usercampaignstatus)
        res = coll.find_one(query)

    if res:
        res["_id"] = str(res["_id"])
        return res
    else:
        return {"error": "Not found"}


def post_user_campaign_status(body):
    if "campaign_status" in body:
        for ele in body["campaign_status"]:
            if "date" in ele:
                ele["date"] = milliseconds_since_epoch_to_datetime(ele["date"])
    if "claim_status" in body:
        for ele in body["user_claims"]:
            if "claim_date" in ele:
                ele["claim_date"] = milliseconds_since_epoch_to_datetime(
                    ele["claim_date"]
                )

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_usercampaignstatus)
        result = coll.insert_one(body)

    return result.acknowledged


def patch_user_campaign_status(campaignId: str, userId: str, body):
    try:
        query = {"campaign_id": campaignId, "user_id": userId}
    except:
        return {"error": "Bad campaign id or user id"}

    if "campaign_status" in body:
        for ele in body["campaign_status"]:
            if "date" in ele:
                ele["date"] = milliseconds_since_epoch_to_datetime(ele["date"])
    if "user_claims" in body:
        for ele in body["user_claims"]:
            if "claim_date" in ele:
                ele["claim_date"] = milliseconds_since_epoch_to_datetime(
                    ele["claim_date"]
                )

    if "campaign_status" in body.keys() and "user_claims" in body.keys():
        change = {
            "campaign_id": campaignId,
            "user_id": userId,
            "campaign_status": body["campaign_status"],
            "user_claims": body["user_claims"],
        }
    elif "campaign_status" in body.keys():
        change = {
            "campaign_id": campaignId,
            "user_id": userId,
            "campaign_status": body["campaign_status"],
        }
    elif "user_claims" in body.keys():
        change = {
            "campaign_id": campaignId,
            "user_id": userId,
            "user_claims": body["user_claims"],
        }
    else:
        change = None

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_usercampaignstatus)

        if change != None:
            res = coll.update_one(query, {"$set": change}, upsert=True)
        else:
            res = None

    if res:
        result = get_user_campaign_status(campaignId, userId)
        return result
    else:
        return {"error": "Not found"}


def patch_append_user_claims(campaignId: str, userId: str, claim):
    try:
        query = {"campaign_id": campaignId, "user_id": userId}
    except:
        return {"error": "Bad campaign id or user id"}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_usercampaignstatus)
        res = coll.update_one(
            query, {"$push": {"user_claims": claim}}, upsert=True)

    if res:
        result = get_user_campaign_status(campaignId, userId)
        return result
    else:
        return {"error": "Not found"}


def post_feedback(body):
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        # creates collection if does not exist
        coll = db[coll_feedback]
        feedback = {
            "location": body["location"],
            "rating": body["rating"],
            "issue": body["issue"],
            "created": datetime.datetime.now(tz=tz_utc),
        }
        if "machine_id" in body:
            feedback["machine_id"] = body["machine_id"]
        result = coll.insert_one(feedback)

    if result.acknowledged:
        return {"message": "Feedback posted"}
    else:
        return {"error": "Failed to post feedback"}
        return {"error": "Not found"}


def post_feedbackv2(body):
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        # creates collection if does not exist
        coll = db[coll_feedback]
        feedback = {
            "location": body["location"],
            "feedback_id": body["feedback_id"],
            "questions": body["questions"],
            "exercise_ids": body["exercise_ids"],
            "type": body["type"],
            "created": datetime.datetime.now(tz=tz_utc),
        }
        if "machine_id" in body:
            feedback["machine_id"] = body["machine_id"]
        result = coll.insert_one(feedback)

    if result.acknowledged:
        return {"message": "Feedback posted"}
    else:
        return {"error": "Failed to post feedback"}
        return {"error": "Not found"}


def post_feedback_question(body):
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        # creates collection if does not exist
        coll = db[coll_feedback_question]
        feedback = {
            "questions": body["questions"],
            "location": body["location"],
            "type": body["type"],
            "created": datetime.datetime.now(tz=tz_utc),
        }
        result = coll.insert_one(feedback)

    if result.acknowledged:
        return {"message": "Feedback posted"}
    else:
        return {"error": "Failed to post feedback"}
        return {"error": "Not found"}


def get_feedback_question(type):
    try:
        query = {"type": type}
    except:
        return {"error": "invalid type"}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_feedback_question)
        res = coll.find(query).sort('created', -1)

    if res:
        collList = list(res)
        for elem in collList:
            elem["_id"] = str(elem["_id"])
        return collList
    else:
        return {"error": "Not found"}


def get_all_wearable_details(userId: str):
    query_params = []
    query_params.append({"user_id": userId})
    query = {"$match": {"$and": query_params}}
    projection = {
        "$project": {
            "_id": 0,
            "user_id": 1,
            "last_updated": 1,
            "peripheral_name": 1,
            "peripheral_id": 1,
            "peripheral_model": 1,
        }
    }
    sort = {"$sort": {"last_updated": pymongo.DESCENDING}}
    pipeline = [query, projection, sort]

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_wearable_details)
        res = coll.aggregate(pipeline)

    res_list = list(res)
    if res_list:
        return {"success": "All wearable details retrieved", "status_code": 200, "data": res_list}
    else:
        return {"error": "not found", "status_code": 404, "data": {}}


def get_one_wearable_details(userId: str, wearableId: str):

    query = {"$and": [{"user_id": userId}, {"peripheral_id": wearableId}]}
    # query = {"user_id": userId, "peripheral_id": wearableId}
    projection = {
        "_id": 0,
        "user_id": 1,
        "last_updated": 1,
        "peripheral_name": 1,
        "peripheral_id": 1,
        "peripheral_model": 1,
    }

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_wearable_details)
        res = coll.find_one(query, projection)

    if res:
        return {"success": "All wearable details retrieved", "status_code": 200, "data": res}
    else:
        return {"error": "not found", "status_code": 404, "data": {}}


def update_wearable_details(body):
    seconds_since_epoch = datetime.datetime.now(tz_utc).timestamp() * 1000
    body.update({"last_updated": seconds_since_epoch})
    query = {"user_id": body["user_id"],
             "peripheral_model": body["peripheral_model"]}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_wearable_details)
        res = coll.update_one(query, {"$set": body}, upsert=True)

    # try:
    #     matchedCount = res.matched_count
    #     modifiedCount = res.modified_count
    #     upsertedId = res.upserted_id
    #     acknowledged = res.acknowledged

    #     return {
    #         "Success": "Wearable Details Updated",
    #         "Data":
    #             {
    #                 "matchedCount" : matchedCount,
    #                 "modifiedCount" :modifiedCount,
    #                 "upsertedId":  upsertedId,
    #                 "acknowledged" : acknowledged,
    #             }
    #         }

    # except:
    #     return {"Success": "New Wearable Added"}

    if not res.upserted_id:
        return {"success": "Wearable details updated",
                "status_code": 200,
                "data": {"upserted_id": res.upserted_id}}

    else:
        return {"success": "New wearable detail added",
                "status_code": 201,
                "data": {"upserted_id": res.upserted_id}}


def delete_wearable_details(userId: str, wearableId: str):
    query = {"user_id": userId, "peripheral_id": wearableId}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_wearable_details)
        res = coll.delete_one(query)

    if res.deleted_count > 0:
        return {"success": "Wearable detail deleted",
                "status_code": 200,
                "data": {"deleted_count": res.deleted_count}}

    else:
        return {'error': 'Wearable details not found',
                "status_code": 404,
                'data': {
                    'delete_count': res.deleted_count}}

def get_all_wearable_data(
    userId: str, dataType: str, startDate: int, endDate: int
):
    # TODO: check date

    query_params = []
    query_params.append({"user_id": userId})
    if dataType:
        query_params.append({"data_type": dataType})
    if startDate:
        query_params.append({"date": {"$gte": startDate}})
    if endDate:
        query_params.append({"date": {"$lt": endDate}})

    query = {"$match": {"$and": query_params}}
    projection = {
        "$project": {
            "_id": 0,
            "user_id": 1,
            "wearable_id": 1,
            "date": 1,
            "data_type": 1,
            "packets": 1,
        }
    }
    sort = {"$sort": {"date": pymongo.DESCENDING}}
    pipeline = [query, projection, sort]

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_wearable_data)
        res = coll.aggregate(pipeline)

    res_list = list(res)
    if res_list:
        return {"success": "Wearable data retrieved", "status_code": 200, "data": res_list}
    else:
        return {"error": "not found", "status_code": 404, "data": {}}


def get_wearable_data(
    userId: str, wearableId: str, dataType: str, startDate: int, endDate: int
):
    # TODO: check date

    query_params = []
    query_params.append({"user_id": userId})
    query_params.append({"wearable_id": wearableId})
    if dataType:
        query_params.append({"data_type": dataType})
    if startDate:
        query_params.append({"date": {"$gte": startDate}})
    if endDate:
        query_params.append({"date": {"$lt": endDate}})

    query = {"$match": {"$and": query_params}}
    projection = {
        "$project": {
            "_id": 0,
            "user_id": 1,
            "wearable_id": 1,
            "date": 1,
            "data_type": 1,
            "packets": 1,
        }
    }
    sort = {"$sort": {"date": pymongo.DESCENDING}}
    pipeline = [query, projection, sort]

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_wearable_data)
        res = coll.aggregate(pipeline)

    res_list = list(res)
    if res_list:
        return {"success": "Wearable data retrieved", "status_code": 200, "data": res_list}
    else:
        return {"error": "not found", "status_code": 404, "data": {}}


# Try to find wearable packets with timestamps that is within start/end time of exercise
# Sync and add wearable data (hr, hr zone, steps) into exercise data in exercise collection
# Print an error msg if syncing fails
#
# Will also store wearable data in wearable data collection
# Returns res.acknowledge if operation is successful


def update_wearable_data(userId: str, wearableId: str, body: dict):
    # Get user age, currently using dummy age of 30
    age = _get_age_from_user(userId)

    # Add wearable data to exercise collection
    _sync_exercise_wearable(
        wearable_packets=body["packets"],
        detailed_exercises=_get_exercise_with_wearable_data(userId, body),
        datatype=body["data_type"],
        age=age,
    )

    # Update wearable data to wearable collection
    seconds_since_epoch = datetime.datetime.now(tz_utc).timestamp() * 1000
    body.update({"last_updated": seconds_since_epoch})
    query = {
        "user_id": userId,
        "wearable_id": wearableId,
        "date": body["date"],
        "data_type": body["data_type"],
    }

    body.update({"user_id": userId})
    body.update({"wearable_id": wearableId})

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_wearable_data)
        res = coll.update_one(query, {"$set": body}, upsert=True)

    if not res.upserted_id:
        return {"success": "Wearable data updated",
                "status_code": 200,
                "data": {"upserted_id": res.upserted_id}}

    else:
        return {"success": "New wearable data added",
                "status_code": 201,
                "data": {"upserted_id": res.upserted_id}}


# Calculate user age from user dob, returns default age if no dob is found


def _get_age_from_user(userId):
    def years(ts):
        # no of seconds in year = 31536000
        return divmod(ts, 31536000)[0]

    user_info = get_user(None, userId)

    try:
        dob = user_info["user_dob"]
        total_seconds = (datetime.datetime.now(tz_utc) - dob).total_seconds()
        age = years(total_seconds)
    except:
        age = 30

    return age


# Pull exercises with timestamp that matches wearable data timestamp


def _get_exercise_with_wearable_data(userId, body):
    # Pull exercise data to update
    start_date = body["date"]
    end_date = body["date"] + datetime.timedelta(days=1).total_seconds() * 1000
    exercise_data = get_user_exercises(
        user="", userId=userId, start_date=start_date, end_date=end_date
    )

    # exercise session contains wearble data
    detailed_exercises = []
    if "res" in exercise_data.keys():
        for ex in exercise_data["res"]:
            id = ex["exercise_id"]
            detailed_exercises.append(
                get_user_exercise_detail(user="", userId=userId, exerciseId=id)
            )

    return detailed_exercises


# Returns a list of duration stored in each hr zone
# hr_zone_dur[0] == duration spent below hr zone 1
# hr_zone_dur[1] ... [5] == duration spent in hr zone 1 -5


def _get_hr_zones(hr, age, ex_duration):
    time_interval = ex_duration / len(hr)
    max_hr = 220 - age
    zone_1 = max_hr * 0.5
    zone_2 = max_hr * 0.6
    zone_3 = max_hr * 0.7
    zone_4 = max_hr * 0.8
    zone_5 = max_hr * 0.9

    bins = [0, zone_1, zone_2, zone_3, zone_4, zone_5, max_hr]
    labels = [0, 1, 2, 3, 4, 5]
    hr_zone_dur = [0 for x in range(len(labels))]

    hr_binned = pd.cut(hr, bins, labels=labels)

    for i in hr_binned:
        hr_zone_dur[i] += time_interval

    return hr_zone_dur


# Uses scipy interpolate for missing data
def _sync_exercise_wearable(wearable_packets, detailed_exercises, datatype, age=30):
    def timestamp_filter(p, ex_start, ex_end, max_diff):
        if abs(p["timestamp"] - ex_start) > max_diff and p["timestamp"] < ex_start:
            return False
        if abs(p["timestamp"] - ex_end) > max_diff and p["timestamp"] > ex_end:
            return False
        # reject if hr == 0
        if datatype == "heartrate":
            if p[datatype] == 0:
                return False

        return True

    def interpolate(x, xp, fp):
        v = np.interp(x, xp, fp)
        return v

    for ex in detailed_exercises:
        ex_start = ex["exercise_started"].timestamp() * 1000
        ex_end = ex["exercise_ended"].timestamp() * 1000

        print(ex_start)

        max_diff = datetime.timedelta(minutes=5).total_seconds() * 1000
        print(max_diff)

        # find wearable packets that is within start/ end time of exercise
        matches = [
            p
            for p in wearable_packets
            if (timestamp_filter(p, ex_start, ex_end, max_diff))
        ]

        # interpolate/ extrapolate data
        x = [(ts["timestamp"].timestamp() * 1000)
             for ts in ex["exercise_data"]]
        xp = [x["timestamp"] for x in matches]  # x axis
        fp = [x[datatype] for x in matches]  # y axis

        # print("--------------------------------------------------")
        # print(ex_start)
        # print(xp)
        # print(fp)

        # Change to np for now as unable to install scipy in new docker img
        # inter_data = interpolate.interp1d(xp, fp, bounds_error=False, fill_value='extrapolate')
        # interpolated_values = inter_data(x)

        if len(xp) > 1:
            interpolated_values = interpolate(x, xp, fp)

            # Caluclate total steps and avg hr
            if datatype == "steps":
                interpolated_values = interpolated_values - \
                    interpolated_values[0]
                ex["exercise_summary"]["total_steps"] = interpolated_values[-1]
            if datatype == "heartrate":
                ex["exercise_summary"]["avg_heartrate"] = sum(
                    interpolated_values
                ) // len(interpolated_values)
                ex["exercise_summary"]["duration_in_heartrate_zone"] = _get_hr_zones(
                    interpolated_values, age, ex_end - ex_start
                )

            for index, data in enumerate(interpolated_values):
                ex["exercise_data"][index][datatype] = data

            # Update exercise collection
            # No user id as the res from get_wearable_details does not contain user_id field
            query = {"_id": ObjectId(ex["exercise_id"])}

            with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
                db = conn[db_gym]
                coll = db.get_collection(coll_exercise)
                res = coll.update(
                    query,
                    {
                        "$set": {
                            "exercise_data": ex["exercise_data"],
                            "exercise_summary": ex["exercise_summary"],
                        }
                    },
                    upsert=True,
                )


def get_exercise_insights(userId):
    return "hello from get_exercise_insights"


def get_user_records(userId: str, exercise_name=""):
    # Query user
    queryParams = []
    queryParams.append({"_id": ObjectId(userId)})
    if exercise_name != "":
        queryParams.append(
            {"computed_1_rep_max.data.exercise_name": exercise_name})

    try:
        query = {"$and": queryParams}

    except Exception:
        return {"error": "Bad userId"}

    # Apply
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_users)
        # cur= coll.aggregate(pipeline)
        # res = coll.find_one(query, proj)
        res = coll.find_one(query)

    final_result = {}

    if res:
        if "computed_1_rep_max" in res:
            for i in range(len(res["computed_1_rep_max"]["data"])):
                result = {}
                if "1_rep_max" in res["computed_1_rep_max"]["data"][i]:
                    result["1_rep_max"] = res["computed_1_rep_max"]["data"][i]["1_rep_max"]

                if "recorded" in res["computed_1_rep_max"]["data"][i]:
                    result["recorded"] = res["computed_1_rep_max"]["data"][i]["recorded"]

                if "exercise_name" in res["computed_1_rep_max"]["data"][i]:
                    result["exercise_name"] = res["computed_1_rep_max"]["data"][i]["exercise_name"]

                    # result.update({"recorded": res["computed_1_rep_max"]["data"]["recorded"]})
                    # result.update({"exercise_name": res["computed_1_rep_max"]["data"]["exercise_name"]})
                if "historical_1_rep_max" in res["computed_1_rep_max"]["data"][i]:
                    result.update(
                        {"historical_1_rep_max": res["computed_1_rep_max"]["data"][i]["historical_1_rep_max"]})
                final_result[res["computed_1_rep_max"]
                             ["data"][i]["exercise_name"]] = result
        res["_id"] = str(res["_id"])

        # return res
        return final_result
    else:
        return {"error": "not found"}  # Return empty Dict


def get_insights_records(userId: str):

    # Pipeline
    user_filter = {
        "$match": {
            "user_id": userId,
        }
    }

    user_records = {
        "$facet": {
            "treadmill": [
                {"$match": {"exercise_type": "treadmill"}},
                {"$group": {
                    "_id": "$user_id",
                    "furthest_dist": {"$max": "$exercise_summary.total_distance"},
                    "fastest_avg_speed": {"$max": "$exercise_summary.avg_speed"},
                    "longest_duration": {"$max": "$exercise_summary.duration"}
                }}
            ],

            "staticbike": [
                {"$match": {"exercise_type": "bike"}},
                {"$group": {
                    "_id": "$user_id",
                    "furthest_dist": {"$max": "$exercise_summary.total_distance"},
                    "fastest_avg_speed": {"$max": "$exercise_summary.avg_speed"},
                    "fastest_avg_cadence": {"$max": "$exercise_summary.avg_cadence"},
                    "longest_duration": {"$max": "$exercise_summary.duration"}
                }}
            ],

            "chestpress": [
                {"$match": {"exercise_name": "Chest Press", }},
                {"$group": {
                    "_id": "$user_id",
                    "highest_chestpress_wt": {"$max": "$exercise_summary.weight"},
                }},
            ],

            "shoulderpress": [
                {"$match": {"exercise_name": "Shoulder Press", }},
                {"$group": {
                    "_id": "$user_id",
                    "highest_shoulderpress_wt": {"$max": "$exercise_summary.weight"},
                }}
            ],

            "legpress": [
                {"$match": {"exercise_name": "Leg Press", }},
                {"$group": {
                    "_id": "$user_id",
                    "highest_legpress_wt": {"$max": "$exercise_summary.weight"},
                }},
            ],

            "legcurl": [
                {"$match": {"exercise_name": "Leg Curl", }},
                {"$group": {
                    "_id": "$user_id",
                    "highest_legcurl_wt": {"$max": "$exercise_summary.weight"},
                }},
            ],

            "legextension": [
                {"$match": {"exercise_name": "Leg Extension", }},
                {"$group": {
                    "_id": "$user_id",
                    "highest_legextension_wt": {"$max": "$exercise_summary.weight"},
                }},
            ]
        }
    }

    records_output = {
        "$project": {
            "userid": "$userId",
            "treadmill": 1,
            "staticbike": 1,
            "chestpress": 1,
            "legpress": 1,
            "shoulderpress": 1,
            "legcurl": 1,
            "legextension": 1
        }
    }

    pipeline = [
        user_filter,
        user_records,
        records_output
    ]

    # Apply
    query = {"$and": [{"user_id": userId}, {"exercise_summary.weight": ch}]}
    projection = {"created": 1}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_exercise)
        cur = coll.aggregate(pipeline)

    # Result
    res = list(cur)
    if res:
        if res[0]['chestpress'] != []:
            highest_chestpress_wt = res[0]['chestpress'][0]["highest_chestpress_wt"]
            query = {"$and": [{"user_id": userId}, {"exercise_name": "Chest Press"}, {
                "exercise_summary.weight": highest_chestpress_wt}]}
            date_res = coll.find_one(
                query,
                projection,
            )
            date_res["created"] = str(date_res["created"])
            res[0]['chestpress'][0]['date'] = date_res["created"]

        if res[0]['shoulderpress'] != []:
            highest_shoulderpress_wt = res[0]['shoulderpress'][0]["highest_shoulderpress_wt"]
            query = {"$and": [{"user_id": userId}, {"exercise_name": "Shoulder Press"}, {
                "exercise_summary.weight": highest_shoulderpress_wt}]}
            date_res = coll.find_one(
                query,
                projection,
            )
            date_res["created"] = str(date_res["created"])
            res[0]['shoulderpress'][0]['date'] = date_res["created"]

        if res[0]['legpress'] != []:
            highest_legpress_wt = res[0]['legpress'][0]["highest_legpress_wt"]
            query = {"$and": [{"user_id": userId}, {"exercise_name": "Leg Press"}, {
                "exercise_summary.weight": highest_legpress_wt}]}
            date_res = coll.find_one(
                query,
                projection,
            )
            date_res["created"] = str(date_res["created"])
            res[0]['legpress'][0]['date'] = date_res["created"]

        if res[0]['legcurl'] != []:
            highest_legcurl_wt = res[0]['legcurl'][0]["highest_legcurl_wt"]
            query = {"$and": [{"user_id": userId}, {"exercise_name": "Leg Curl"}, {
                "exercise_summary.weight": highest_legcurl_wt}]}
            date_res = coll.find_one(
                query,
                projection,
            )
            date_res["created"] = str(date_res["created"])
            res[0]['legcurl'][0]['date'] = date_res["created"]

        if res[0]['legextension'] != []:
            highest_legextension_wt = res[0]['legextension'][0]["highest_legextension_wt"]
            query = {"$and": [{"user_id": userId}, {"exercise_name": "Leg Extension"}, {
                "exercise_summary.weight": highest_legextension_wt}]}
            date_res = coll.find_one(
                query,
                projection,
            )
            date_res["created"] = str(date_res["created"])
            res[0]['legextension'][0]['date'] = date_res["created"]

        if res[0]['treadmill'] != []:
            furthest_dist = res[0]['treadmill'][0]["furthest_dist"]
            query1 = {"$and": [{"user_id": userId}, {"exercise_type": "treadmill"},  {
                "exercise_summary.total_distance": furthest_dist}]}
            date_res1 = coll.find_one(
                query1,
                projection,
            )
            fastest_avg_speed = res[0]['treadmill'][0]["fastest_avg_speed"]
            query2 = {"$and": [{"user_id": userId}, {"exercise_type": "treadmill"}, {
                "exercise_summary.avg_speed": fastest_avg_speed}]}
            date_res2 = coll.find_one(
                query2,
                projection,
            )
            longest_duration = res[0]['treadmill'][0]["longest_duration"]
            query3 = {"$and": [{"user_id": userId}, {"exercise_type": "treadmill"}, {
                "exercise_summary.duration": longest_duration}]}
            date_res3 = coll.find_one(
                query3,
                projection,
            )
            date_res1["created"] = str(date_res1["created"])
            res[0]['treadmill'][0]['furthest_dist_date'] = date_res1["created"]
            date_res2["created"] = str(date_res2["created"])
            res[0]['treadmill'][0]['fastest_avg_speed_date'] = date_res2["created"]
            date_res3["created"] = str(date_res3["created"])
            res[0]['treadmill'][0]['longest_duration_date'] = date_res3["created"]

        if res[0]['staticbike'] != []:
            furthest_dist = res[0]['staticbike'][0]["furthest_dist"]
            query1 = {"$and": [{"user_id": userId}, {"exercise_type": "bike"}, {
                "exercise_summary.total_distance": furthest_dist}]}
            date_res1 = coll.find_one(
                query1,
                projection,
            )

            longest_duration = res[0]['staticbike'][0]["longest_duration"]
            query2 = {"$and": [{"user_id": userId}, {"exercise_type": "bike"}, {
                "exercise_summary.duration": longest_duration}]}
            date_res2 = coll.find_one(
                query2,
                projection,
            )
            fastest_avg_speed = res[0]['staticbike'][0]["fastest_avg_speed"]
            query3 = {"$and": [{"user_id": userId}, {"exercise_type": "bike"}, {
                "exercise_summary.avg_speed": fastest_avg_speed}]}
            date_res3 = coll.find_one(
                query3,
                projection,
            )
            fastest_avg_cadence = res[0]['staticbike'][0]["fastest_avg_cadence"]
            query4 = {"$and": [{"user_id": userId}, {"exercise_type": "bike"}, {
                "exercise_summary.avg_cadence": fastest_avg_cadence}]}
            date_res4 = coll.find_one(
                query4,
                projection,
            )
            date_res1["created"] = str(date_res1["created"])
            res[0]['staticbike'][0]['furthest_dist_date'] = date_res1["created"]
            date_res2["created"] = str(date_res2["created"])
            res[0]['staticbike'][0]['longest_duration_date'] = date_res2["created"]
            date_res3["created"] = str(date_res3["created"])
            res[0]['staticbike'][0]['fastest_avg_speed_date'] = date_res3["created"]
            date_res4["created"] = str(date_res4["created"])
            res[0]['staticbike'][0]['fastest_avg_cadence_date'] = date_res4["created"]

        return res[0]
    else:
        return None


def get_wearable_auth_key(key):
    try:
        result = get_docker_secret(key)
    except:
        return {"error": "error fetching wearable auth key", "status_code": "404", "data": {}}

    return {"success": "Wearable auth key retrieved",
            "status_code": 200,
            "data": result}


def leaderboard_metrics(active: bool = True, location: str = "all", recurring: bool = False):
    """Routes /leaderboard_metrics

    Args:
      location: Requested gym location (default: all)
      active: True or False (default True)
    Returns:
      leaderboard_metrics base on filter in query parameter [active or location]
    """
    time_now = datetime.datetime.now()

    # check for active leaderboard
    if(active):
        filt = {"$and": [{"start_date": {"$lte": time_now}},
                         {"end_date": {"$gte": time_now}}]}

    else:
        filt = {"$and": [
            {"$or": [{"start_date": {"$gte": time_now}}, {"end_date": {"$lte": time_now}}]}]}
    # check for location
    if(location != "all"):
        filt["$and"].append({"data_requirement.locations": location})

    # check for recurring leaderboard
    if(recurring):
        filt = {"$or": [{"$and": [{"recurring": True}, {
            "data_requirement.locations": location}]}, {"$and": filt["$and"]}]}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_leaderboard_metrics,
            # codec_options=options
        )
        results = coll.find(filt)
        results_out = list(results)
        # print(results)
    for x in range(len(results_out)):
        results_out[x]["_id"] = str(results_out[x]["_id"])

    if results_out:
        return results_out
    else:
        return {"error": "leaderboard not found"}


def create_leaderboard_metrics(body: dict):
    try:
        body["start_date"] = milliseconds_since_epoch_to_datetime(body["start_date"]).replace(hour=0, minute=0, second=0)
        body["end_date"] = milliseconds_since_epoch_to_datetime(body["end_date"]).replace(hour=23, minute=59, second=59)
        with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
            db = conn[db_gym]
            coll = db.get_collection(coll_leaderboard_metrics)
            result = coll.insert_one(body)

        return result.acknowledged

    except Exception as e:
        raise (e)
        return {"result" : result}


def update_leaderboard_metrics(body:dict):
    try:
        query = {"_id": ObjectId(body["id"])}
        body["start_date"] = milliseconds_since_epoch_to_datetime(body["start_date"]).replace(hour=0, minute=0, second=0)
        body["end_date"] = milliseconds_since_epoch_to_datetime(body["end_date"]).replace(hour=23, minute=59, second=59)


        with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
            db = conn[db_gym]
            coll = db.get_collection(coll_leaderboard_metrics)
        updt = {
            "$set": {
                "start_date": body["start_date"],
                "end_date": body["end_date"],
                "num_users": body["num_users"],
                "location": body["location"],
                "metric": body["metric"],
                "title": body["title"],
                "asset": body["asset"],
                "recurring": body["recurring"],
                "unit": body["unit"],
                "data_requirement": body["data_requirement"]
            },
        }
        result = coll.update_one(
            query,
            updt,
            upsert=True
        )
        return result.acknowledged
    except Exception as e:
        raise(e)

    


def get_user_id_using_wearable(peripheral_id):
    query = {"peripheral_id": peripheral_id}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_wearable_details)
        res = coll.find_one(query)

    if not res:
        return {"error": "not found"}

    query = {"_id": ObjectId(res["user_id"])}
    
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_users)
        res = coll.find_one(query)

    if res:
        return res["activeSgId"]
    else:
        return {"error": "user not found"}
def delete_leaderboard_metrics(campaignId:str):
    try:
        query_leaderboard = {"_id": ObjectId(campaignId)}
        # Actual query
        with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
            db = conn[db_gym]
            coll_user = db.get_collection(
                coll_leaderboard_metrics,
            )
            result = coll_user.delete_one(query_leaderboard)

        if result.deleted_count >= 1:
            return {
                "leaderboard_delete_count": result.deleted_count,
            }
        else:
            return {"error": "Leaderboard not found"}
    except Exception as e:
        raise(e)

# Active Health Trail
def get_all_aht_checkpoint_details():
    try:
        with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
            db = conn[db_gym]
            coll = db.get_collection(coll_aht_checkpoint_details)
            res = coll.find({}, {'_id':0})

        list_res = list(res)

        if list_res:
            return {"success": "All checkpoint details retrieved", "status_code": 200, "data": list_res}
        else:
            return {"error": "not found", "status_code": 404, "data": {}}

    except Exception as e:
        raise(e) 

def get_one_aht_checkpoint_details(checkpointId : str):
    try:
        query_params = []
        query_params.append({"checkpoint_id": checkpointId})
        query = {"$match": {"$and": query_params}}
        projection = {
            "$project": {
                "_id": 0,
                "checkpoint_id": 1,
                "neighbors": 1,
            }
        }
        sort = {"$sort": {"last_updated": pymongo.DESCENDING}}
        pipeline = [query, projection, sort]

        # Returns all check-in data based on user's wearable_id
        with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
            db = conn[db_gym]
            coll = db.get_collection(coll_aht_checkpoint_details)
            res = coll.aggregate(pipeline)

        list_res = list(res)

        if list_res:
            return {"success": "Checkpoint details retrieved", "status_code": 200, "data": list_res}
        else:
            return {"error": "not found", "status_code": 404, "data": {}}

    except Exception as e:
        raise(e) 

def update_aht_checkpoint_details(body: dict):
    try:
        milli_seconds_since_epoch = datetime.datetime.now(tz_utc).timestamp() * 1000
        body.update({"last_updated": milli_seconds_since_epoch})
        query = {"checkpoint_id": body["checkpoint_id"]}

        with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
            db = conn[db_gym]
            coll = db.get_collection(coll_aht_checkpoint_details)
            res = coll.update_one(query, {"$set": body}, upsert=True)

        if not res.upserted_id:
            return {"success": "Checkpoint details updated",
                    "status_code": 200,
                    "data": {"upserted_id": res.upserted_id}}

        else:
            return {"success": "New checkpoint detail added",
                    "status_code": 201,
                    "data": {"upserted_id": res.upserted_id}}

    except:
        return {"error": "Checkin data already inserted", "status_code": 409, "data": {}}


def get_aht_checkin_data(userId: str):    
    try:
        # Get list of wearable id:
        res = get_all_wearable_details(userId)
        
        if(res['status_code'] == 200):
            wearable_list = res['data']
        else:
            return {"error": "not found", "status_code": 404, "data": {}}
        

        query_params = []
        for wearable in wearable_list:
            query_params.append({"wearable_id": wearable['peripheral_id']})       
        
        query = {"$match": {"$or": query_params}}
        projection = {
            "$project": {
                "_id": 0,
                "datetime": 1,
                "path": 1,
                "overall_distance": 1,
                "overall_time_in_seconds": 1,
                "overall_gait_speed": 1,
                "gait_speeds": 1,
                "wearable_id": 1,
            }
        }
        sort = {"$sort": {"datetime": pymongo.DESCENDING}}
        pipeline = [query, projection, sort]

        # Returns all check-in data based on user's wearable_id
        with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
            db = conn[db_gym]
            coll = db.get_collection(coll_aht_trails_data)
            res = coll.aggregate(pipeline)
        
        list_res = list(res)

        if list_res:
            return {"success": "All checkpoint data retrieved", "status_code": 200, "data": list_res}
        else:
            return {"error": "not found", "status_code": 404, "data": {}}

    except Exception as e:
        raise(e)

# Sorts checkin data based on wearable and trails
# def _sort_checkin_data_based_by_wearable_to_trails(checkins:list):
#     to_return = {}
#     threshold_ms = 600000 # 10 mins
#     min_repeat_threshold_ms = 60000
#     for checkin in checkins:
#         wearable_id = checkin['wearable_id']
#         last_updated = checkin['last_updated']
#         checkpoint_id = checkin['checkpoint_id']
#         # TO DO - Find a way to segregate the different trails
#         if wearable_id not in to_return:
#             to_return[wearable_id]= []
#             to_return[wearable_id].append([{'checkpoint_id': checkpoint_id, 'timestamp': last_updated}])

        
#         else:
#             # Check if timestamp of this packet is > X value -> New trail
#             if abs(last_updated - to_return[wearable_id][-1][-1]['timestamp']) > threshold_ms:
#                 to_return[wearable_id].append([{'checkpoint_id': checkpoint_id, 'timestamp': last_updated}])
#             else:
#                 # Check to see if previous checkpoint is same as the one just tapped
#                 if to_return[wearable_id][-1][-1]['checkpoint_id'] == checkpoint_id:
#                     # If timestamp difference is < 60s, it is an additional scan
#                     if abs(to_return[wearable_id][-1][-1]['timestamp'] - last_updated) > min_repeat_threshold_ms:
#                         # Mark as new trail
#                         to_return[wearable_id].append([{'checkpoint_id': checkpoint_id, 'timestamp': last_updated}])
                
#                 # Rule - User cannot skip > 1 subsequent checkpoint -> Create new trail
#                 elif not (_is_neighbor(to_return[wearable_id][-1][-1]['checkpoint_id'], checkpoint_id) or _is_skip_one(to_return[wearable_id][-1][-1]['checkpoint_id'], checkpoint_id)):
#                     to_return[wearable_id].append([{'checkpoint_id': checkpoint_id, 'timestamp': last_updated}])



#                 else:
#                     to_return[wearable_id][-1].append({'checkpoint_id': checkpoint_id, 'timestamp': last_updated})

#     return to_return

# Takes in the sorted checkin for a single trail and returns the overall gait speed, breakdown of gaitspeed between each checkin, path taken, time taken
"""
{
    wearable_id: '111' ,
    trails:[
        datetime: ,
        overall_distance: X,
        overall_time: Y,
        overall_gait_speed: X/Y,
        path: [],
        gait_speeds: [{'ts', 'from', 'to', 'time_taken', 'gait_speed', 'distance'},] }
    ]
}

"""


def _eval_trail(trail: list):
    # Initialise
    pre = None
    path = []
    start_date = milliseconds_since_epoch_to_datetime(trail[0]['timestamp'])
    total_distance, total_time_in_seconds = 0, 0
    gait_speeds = []
    distance_dict = _gen_distance_dict()
    for checkin in trail:
        path.append(checkin['checkpoint_id'])
    total_time_in_seconds = abs(trail[-1]['timestamp'] - trail[0]['timestamp'])/1000

    if len(trail) == 1:
        return {'start_date': start_date , 'path': path, 'total_distance': total_distance, 'total_time_in_seconds': total_time_in_seconds, 'average_gait_speed': 0,  'gait_speeds': [{'from': path[0], 'to': '-', 'timestamp': trail[0]['timestamp'], 'time_taken': 0, 'distance': 0, 'gait_speed': 0}]}

    # For length of path
    for i in range(len(trail)-1):   
        time_taken = abs(trail[i+1]['timestamp'] - trail[i]['timestamp'])/1000
        timestamp = trail[i]['timestamp']

        if(path[i+1] in distance_dict[path[i]]):
            distance = distance_dict[path[i]][path[i+1]]
        
        else:
            distance = _handle_missing_checkin(distance_dict, time_taken, path[i], path[i+1])
        
        
        gait_speeds.append({'from': path[i], 'to':path[i+1], 'timestamp': timestamp, 'time_taken': time_taken, 'distance': distance, 'gait_speed': distance/time_taken})
        
        total_distance += distance
           
    gait_speeds.append({'from': path[-1], 'to': '-', 'timestamp': trail[-1]['timestamp'], 'time_taken': 0, 'distance': 0, 'gait_speed': 0})
    return {'start_date': start_date, 'path': path, 'total_distance': total_distance, 'total_time_in_seconds': total_time_in_seconds, 'average_gait_speed': total_distance/total_time_in_seconds,  'gait_speeds': gait_speeds}





def _gen_distance_dict():
    try:
        res = get_all_aht_checkpoint_details()
        list_of_checkpoints = res['data']
        to_return = {}
        for checkpoint in list_of_checkpoints:
            to_return[checkpoint['checkpoint_id']]  = {}
            for neighbor in checkpoint['neighbors']:
                to_return[checkpoint['checkpoint_id']][neighbor['checkpoint_id']] = neighbor['distance']

        return to_return
    
    except Exception as e:
        raise(e)

def _is_neighbor(checkpoint_1: str, checkpoint_2: str):
    try:
        checkpoint_1_neighbors = get_one_aht_checkpoint_details(checkpoint_1)['data'][0]['neighbors']
        return any(checkpoint['checkpoint_id'] == checkpoint_2 for checkpoint in checkpoint_1_neighbors)
    except Exception as e:
        raise(e)

def _is_skip_one(checkpoint_1: str, checkpoint_2: str):
    try:
        # Find neighbors of CP1
        checkpoint_1_neighbors = get_one_aht_checkpoint_details(checkpoint_1)['data'][0]['neighbors']
        # Find neighbors of neighbors
        for neighbor in checkpoint_1_neighbors:
            # Check if CP2 is in any of them
            if _is_neighbor(neighbor['checkpoint_id'], checkpoint_2):
                return True        
        return False

    except Exception as e:
        raise(e)

def _handle_missing_checkin(distance_dict, time_taken, s, e):
    # Map possible path that user took. Use time as a gauge to determine what path? Possible to get user's average gait speed?
    avg_gait_speed = 1 #m/s
    est_distance = avg_gait_speed * time_taken
    min_diff = float('inf')
    intermediate_checkpoint = ''
    distance_to_return = 0
    # Find possible intermediate checkpoint(s)
    for neighbor in distance_dict[s]:
        if _is_neighbor(neighbor, e):
            # Find distance for each intermediate
            print(distance_dict[s][neighbor])
            print(distance_dict[neighbor][e])
            dist = distance_dict[s][neighbor] + distance_dict[neighbor][e]
            print(dist)
            # Choose which one
            if(min_diff > (abs(est_distance - dist))):
                min_diff = abs(est_distance - dist)
                intermediate_checkpoint = neighbor
                distance_to_return = dist
    
    return distance_to_return

def update_aht_checkin_data(body:dict):
    try:        
        milli_seconds_since_epoch = datetime.datetime.now(tz_utc).timestamp() * 1000
        body.update({"last_updated": milli_seconds_since_epoch})
        result = _is_new_trail(body['wearable_id'], body['checkpoint_id'], body['last_updated'])
        print(result)
        # return result
        # Do checks -> Determine if we update an old list of checkins or create a new one
        if result == None:
            new_trail = _eval_trail([{'checkpoint_id': body['checkpoint_id'], 'timestamp':body['last_updated']}])
            new_trail['wearable_id'] = body['wearable_id']
            
            with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
                db = conn[db_gym]
                coll = db.get_collection(coll_aht_trails_data)
                res = coll.insert_one(new_trail)

            if res.acknowledged:
                return {"success": "New trail created",
                        "status_code": 201,
                        "data": {"acknowledged": res.acknowledged}}
        # Get latest one and update
        elif result != -1:
            # Add latest checkin-data into the trail
            _id = result['_id']
            path = result["path"]
            dt = result["start_date"]
            gait_speeds = result["gait_speeds"]
            overall_distance = result["total_distance"]
            overall_gait_speed = result["average_gait_speed"]
            overall_time_in_seconds = result["total_time_in_seconds"]
            
            list_trail = []
            for item in gait_speeds:
                list_trail.append({'checkpoint_id': item['from'], 'timestamp':item['timestamp']})

            list_trail.append({'checkpoint_id': body['checkpoint_id'], 'timestamp':body['last_updated']})
            # Modify data
            new_trail = _eval_trail(list_trail)
            print(new_trail)
            new_trail['wearable_id'] = body['wearable_id']
            query = {'_id': _id}
            with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
                db = conn[db_gym]
                coll = db.get_collection(coll_aht_trails_data)
                res = coll.update_one(query, {"$set": new_trail}, upsert=False)

            
            if res.acknowledged:
                return {"success": "Updated trail",
                        "status_code": 200,
                        "data": {"acknowledged": res.acknowledged}}
    except Exception as e:
        print("Error: ", e)         

def _is_new_trail(wearable_id: str, checkpoint_id: str, last_updated: int):
    try:
        query_params = []
        query_params.append({'wearable_id': wearable_id})

        
        query = {"$match": {"$and": query_params}}
        projection = {
            "$project": {
                "_id": 1,
                "path": 1,
                "wearable_id": 1,
                "start_date": 1,
                "gait_speeds":1,
                "total_distance": 1,
                "average_gait_speed": 1,
                "total_time_in_seconds": 1,
            }
        }
        sort = {"$sort": {"start_date": pymongo.DESCENDING}}
        pipeline = [query, projection, sort]

        # Returns all check-in data based on user's wearable_id
        with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
            db = conn[db_gym]
            coll = db.get_collection(coll_aht_trails_data)
            res = coll.aggregate(pipeline)
        
        latest_trail = list(res)[0]
   

        return _is_part_of_trail(latest_trail, checkpoint_id, last_updated)
        

    
    except:
        return None

def _is_part_of_trail(trail, checkpoint_id: str, last_updated: int):
    last_checkpoint = trail['path'][-1]
    last_trail_ts = trail['gait_speeds'][-1]['timestamp']
    print("Last trail TS: ", last_trail_ts)
    print("Current: ", last_updated)
    print(abs(last_updated - last_trail_ts))
    threshold_ms = 600000 # 10 mins
    min_repeat_threshold_ms = 60000 # 1 min
    # Check timing
    if abs(last_updated - last_trail_ts) > threshold_ms:
        print("Beyond thresh")
        return None

    else:
        # Check to see if previous checkpoint is same as the one just tapped
        if last_checkpoint == checkpoint_id:
            # If timestamp difference is < 60s, it is an additional scan
            if abs(last_trail_ts - last_updated) < min_repeat_threshold_ms:
                print("Repeated Scan")
                return -1
            
            else:
                return None

    # Check neighbor
    if _is_neighbor(last_checkpoint, checkpoint_id) or _is_skip_one(last_checkpoint, checkpoint_id):
        return trail
