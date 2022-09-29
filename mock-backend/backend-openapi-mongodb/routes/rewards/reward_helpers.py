import random
import logging

import pymongo
from bson.objectid import ObjectId
from bson.codec_options import CodecOptions

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
# logger.setLevel(logging.WARNING)
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)
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
postgres_rewards_table = "rewards"
postgres_rewards_quantity_col = "quantity"
postgres_rewards_id_col = "uuid"
postgres_event_id_col = "event_id"
postgres_event_type_col = "event_collection"
postgres_rewards_name_col = "reward_name"

mongo_ip = "mongodb"
mongo_port = 27017
db_gym = "gym"  
coll_rewardselections = 'rewardselections'
reward_selections_reward_uuids = 'reward_uuids'

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


def get_random_reward(reward_selection_id: str):
    
    #### get list of reward uuids
    mongo_query = {
        '_id': ObjectId(reward_selection_id)
    }
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(coll_rewardselections)
        res = coll.find_one(mongo_query)
    rewards_uuids = tuple([str(id) for id in list(res[reward_selections_reward_uuids])])
    # print(rewards_uuids)

    #### get qty of selected rewards
    postgres_query = f'''SELECT {postgres_rewards_id_col},{postgres_rewards_name_col},{postgres_rewards_quantity_col} 
                        FROM {postgres_rewards_table}
                        WHERE {postgres_rewards_id_col} in {rewards_uuids};'''            
    with PDB(postgres_user, postgres_pw, postgres_db, postgres_ip) as conn:
        c = conn.cursor()
        c.execute(postgres_query)
        result = c.fetchall()
    # print(result)

    if result:
        #### expand reward list
        rewards = []
        for reward in result:
            reward_uuid = reward[0]
            reward_name = reward[1]
            reward_qty = reward[2]
            for i in range(reward_qty):
                rewards.append({
                    "uuid": reward_uuid,
                    "reward_name": reward_name
                })
        # print((rewards))
        # print(len(rewards))

        #### return random entry in expanded reward list
        return random.choice(rewards)
    
    else:
        return {"error": "Not found"}


def decrement_reward_quantity(reward_uuid:str, event_id, event_type):
    print(reward_uuid)
    if event_id != None and event_type!=None:
        postgres_query = f'''UPDATE {postgres_rewards_table}
                            SET {postgres_rewards_quantity_col} = {postgres_rewards_quantity_col} - 1
                            WHERE {postgres_rewards_id_col} = '{reward_uuid}' AND 
                            {postgres_event_id_col} LIKE '%{event_id}%' AND
                            {postgres_event_type_col} = '{event_type}';''' 
    else:
        postgres_query = f'''UPDATE {postgres_rewards_table}
                            SET {postgres_rewards_quantity_col} = {postgres_rewards_quantity_col} - 1
                            WHERE {postgres_rewards_id_col} = '{reward_uuid}';''' 
    print(postgres_query)
    with PDB(postgres_user, postgres_pw, postgres_db, postgres_ip) as conn:
        c = conn.cursor()
        c.execute(postgres_query)
        updated_rows = c.rowcount
    
    if updated_rows:
        return {'updated_rows': updated_rows}
    else: 
        return {"error": "Not found"}