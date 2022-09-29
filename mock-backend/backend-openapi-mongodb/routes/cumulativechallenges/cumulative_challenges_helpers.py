import logging
import time
import os
import json
import pytz
import redis
import pymongo
from pymongo import results
from bson.objectid import ObjectId
from bson.codec_options import CodecOptions
from datetime import datetime
import pika


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
# test

# Set up logger
logger = logging.getLogger(__name__)
# logger.setLevel(logging.WARNING)
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.ERROR)
ch = logging.StreamHandler()
format_str = '%(levelname)s:%(lineno)s:%(message)s'
formatter = logging.Formatter(format_str)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info('Logger ready')

def get_secret(secret_name):
    try:
        with open(f'/run/secrets/{secret_name}', 'r') as secret_file:
            return secret_file.read().splitlines()[0]
    except IOError:
        raise

mongo_user = get_secret('SMARTGYM_USER')
mongo_password = get_secret('SMARTGYM_PASSWORD')

#mongodb parameter
mongo_ip = "mongodb"
mongo_port = 27017
db_gym = "gym"
coll_exercise = "exercises"
coll_bodymetrics = "bodymetrics"
coll_campaigns = "campaigns"
coll_usercampaignstatus = "usercampaignstatus"
coll_users = "users"
coll_apikeys = "apikeys"
coll_accesstokens = "accesstokens"
coll_refreshtokens = "refreshtokens"
coll_wearable_details = "wearabledetails"
coll_wearable_data = "wearabledata"
coll_cumulative_challenges = "cumulative_challenges"
coll_user_cumulative_challenge_status = "user_cumulative_challenge_status"
tz_sg = pytz.timezone("Singapore")
tz_utc = pytz.timezone("UTC")
options = CodecOptions(tz_aware=True, tzinfo=tz_utc)


redis_ip = "redis"
redis_port = 6379
channel_cumulative_challenge_calculation = "cumulative-challenge-computation"
r = redis.Redis(host=redis_ip, port=redis_port)

rabbitmq_ip = 'rabbitmq'
rabbitmq_port = 5672
rabbitmq_user = "user"
rabbitmq_pw = "bitnami"
rabbitmq_processing_queue = "process"

class MDB:
    def __init__(self, ip: str, port: int, username: str, password: str):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

    def __enter__(self):
        from pymongo import MongoClient
        self.client = MongoClient(self.ip, self.port, username=self.username, password=self.password)
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


def mongo_cumulative_challenges(
    location: str,
    active: bool
    ):
    #filters
    query = {}

    if(location != "all"):
        query = {**query,"location": location}

    if active != None:
        if active:
            query = {
                    **query,
                    'start_date':{
                        '$lte': datetime.now()
                    },
                    'end_date':{
                        '$gte': datetime.now()
                    }
                }    
        else:
            query = {
                **query,
                "$or": [
                    {"start_date": {"$gte": datetime.now()}}, 
                    {"end_date": {"$lt": datetime.now()}}
                ]
            }

    sort = {
        'end_date': pymongo.DESCENDING
    }

    pipeline = [{"$match":query}, {'$sort':sort}]

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_cumulative_challenges,
            # codec_options=options
        )
        results = coll.aggregate(pipeline)
    
    # Post processing
    if results:
        collList = list(results)
        for elem in collList:
            elem["_id"] = str(elem["_id"])
        return {"res": collList}
    else:
        return {"error": "Not found"}
    

def mongo_cumulative_challenges_status(user_id: str, cumulative_challenge_id: str ):
    #filters
    query = {"user_id": user_id}
    if(cumulative_challenge_id != ""):
        query = {**query,"cumulative_challenge_id": cumulative_challenge_id}

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_user_cumulative_challenge_status,
            # codec_options=options
        )
        results = coll.find(query)
    if results:
        collList = list(results)
        for elem in collList:
            elem["_id"] = str(elem["_id"])
        return {"res": collList}
    else:
        return {"error": "Not found"}
    


def dispatch_cumulative_challenge_calculation(user_id, location, target):

    logger.debug(f"dispatch_cumulative_challenge_calculation start: {location}")

    payload_data = {
        "user_id": user_id, 
        "location": location, 
        "target": target, 
        "type": "cumulative-challenge-computation"
    }
    payload_data = json.dumps(payload_data)

    revert = bool(os.getenv('REVERT_STAGE3', False))
    if revert:
        numof_subs = r.publish(channel_cumulative_challenge_calculation, payload_data)
        msg = f"Dispatched cumulative challenge calculation for {user_id} in {location} to {numof_subs} subscribers"

    else:
        with RMQ(rabbitmq_ip, rabbitmq_port, rabbitmq_user, rabbitmq_pw) as conn:
            channel = conn.channel() 
            # channel.queue_delete(queue=queue)
            channel.queue_declare(queue=rabbitmq_processing_queue,durable=True)
            channel.basic_publish(exchange='',
                                routing_key=rabbitmq_processing_queue,
                                body=payload_data,
                                properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
                                )
            msg = f"Dispatched cumulative challenge calculation to {rabbitmq_processing_queue} rabbitmq queue"

    logger.info(msg)
    return msg

def get_user_cumulative_challenge_status(cumulative_challenge_id: str, user_id: str):
    try:
        query = {"$and": [{"cumulative_challenge_id": cumulative_challenge_id}, {"user_id": user_id}]}
    except:
        return {"error": "Bad cumulative_challenge_id or user id"}

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_user_cumulative_challenge_status)
        res = coll.find_one(query)

    if res:
        res["_id"] = str(res["_id"])
        return res
    else:
        return {"error": "Not found"}

def patch_append_user_claims(cumulative_challenge_id: str, user_id: str, claim):
    try:
        query = {"cumulative_challenge_id": cumulative_challenge_id, "user_id": user_id}
    except:
        return {"error": "Bad campaign id or user id"}
    
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_user_cumulative_challenge_status)
        res = coll.update_one(query, {"$push": {'user_claims': claim}}, upsert=True)

    if res:
        result = get_user_cumulative_challenge_status(cumulative_challenge_id, user_id)
        return result
    else:
        return {"error": "Not found"}