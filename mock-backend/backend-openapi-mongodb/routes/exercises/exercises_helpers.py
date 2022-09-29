import logging
import pytz
import datetime

import pandas as pd

import pymongo
from bson.codec_options import CodecOptions
from bson.objectid import ObjectId

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
# logger.setLevel(logging.WARNING)
# logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
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

mongo_ip = "mongodb"
mongo_port = 27017
db_gym = "gym"
coll_exercise = "exercises"
coll_users = "users"
coll_bodymetrics = "bodymetrics"

postgres_user = get_secret('SMARTGYM_USER')
postgres_password = get_secret('SMARTGYM_PASSWORD')
postgres_db = 'smartgym'
postgres_ip = 'postgres'
postgres_machines_table = 'machines'

tz_sg = pytz.timezone("Singapore")
tz_utc = pytz.timezone("UTC")
options = CodecOptions(tz_aware=True, tzinfo=tz_utc)

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
def milliseconds_since_epoch_to_datetime(millisecondsSinceEpoch):
    return datetime.datetime.utcfromtimestamp(millisecondsSinceEpoch / 1000)


def exercise_name_to_exercise_type(exercise_name):
    query = f"SELECT type FROM machines \
        WHERE exercise_name LIKE '%{exercise_name}%'"
    with PDB(postgres_user, postgres_password, postgres_db, postgres_ip) as conn:
        c = conn.cursor()
        c.execute(query)
        row = c.fetchall()[0]

    return row[0]

def get_ten_rep_first_quartile(exercise_name, location):
    if location:
        query = f"SELECT DISTINCT exercise_name, ten_rep_first_quartile FROM machine_statistics \
            WHERE exercise_name='{exercise_name}' AND location='{location}';"
    else:
        query = f"SELECT DISTINCT exercise_name, ten_rep_first_quartile FROM machine_statistics \
            WHERE exercise_name='{exercise_name}';"
    with PDB(postgres_user, postgres_password, postgres_db, postgres_ip) as conn:
        c = conn.cursor()
        c.execute(query)
        rows = c.fetchall()
    
    row = rows[0]

    ## if there are multiple location possibilities, choose the min that is non-zero
    if len(rows)>1:
        min_trfq = 999999
        for i,r in enumerate(rows):
            if float(r[1]) == 0:
                continue
            else:
                if float(r[1])<min_trfq:
                    min_trfq = float(r[1])
                    row = rows[i]
    
    ten_rep_first_quartile = float(row[1])
    return ten_rep_first_quartile
    

def exercise_name_to_exercise_group(exercise_name):
    query = f"SELECT DISTINCT exercise_name, exercise_group FROM machines \
        WHERE exercise_name LIKE '%{exercise_name}%';"
    with PDB(postgres_user, postgres_password, postgres_db, postgres_ip) as conn:
        c = conn.cursor()
        c.execute(query)
        rows = c.fetchall()

    row = rows[0]
    ## if there are multiple sub-string possibilities, e.g. legcurl and seatedlegcurl
    if len(rows)>1:
        for i,r in enumerate(rows):
            if str(r[0]).strip() == exercise_name:
                row = rows[i]
        
    ## multi-value column support
    exercise_name_list = [ex_name.strip() for ex_name in row[0].split(',')]
    exercise_group_list = [ex_group.strip() for ex_group in row[1].split(',')]
    return exercise_group_list[exercise_name_list.index(exercise_name)]


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
        body["start_date"] = milliseconds_since_epoch_to_datetime(body["start_date"])

    if "end_date" in body:
        body["end_date"] = milliseconds_since_epoch_to_datetime(body["end_date"])

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

def aggregate_by_time(exercise_list, freq):
    # Do aggregate in pandas because it is more straightforward than
    # mongoDB pipelines
    df = pd.DataFrame(exercise_list)
    tmp = df.groupby(pd.Grouper(key="exercise_started", freq=freq)).sum()
    tmp.reset_index(inplace=True)  # make the index a column

    # Construct return value
    return {
        "user_nickname": exercise_list[0]["user_nickname"],
        "aggregateBy": freq,
        "data": tmp.to_dict("records"),
    }

def get_exercise(username, sort_date_by, aggregate_by):
    # Query user
    query = {"user_nickname": username}

    # Parse date sort
    if sort_date_by == "DESC":
        mongo_sort = pymongo.DESCENDING
    elif sort_date_by == "ASC":
        mongo_sort = pymongo.ASCENDING

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_exercise,
            # codec_options=options
        )
        cur = coll.find(query).sort("exercise_started", mongo_sort)
    cur_list = list(cur)

    if len(cur_list) == 0:
        return cur_list

    # Do aggregate
    if aggregate_by == "none":
        return cur_list
    elif aggregate_by == "day":
        return aggregate_by_time(cur_list, "d")


def post_exercise(body):
    # Handle datetime
    body = validate_datetime(body)

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_exercise,
            # codec_options=options
        )
        result = coll.insert_one(body)

    return result


def post_bodymetrics_entry(body):

    body = validate_datetime(body)

    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_bodymetrics,
            # codec_options=options
        )
        result = coll.insert_one(body)

    return result.acknowledged


