
import math
import datetime
from random import random
import pandas as pd
import random 
from .exercises_helpers import *
from .treadmill_recommendations.vo2max_recommendation import vo2MaxRunIntensityRecommendation
import enum

# Set up logger
logger = logging.getLogger(__name__)
# logger.setLevel(logging.ERROR)
# logger.setLevel(logging.WARNING)
# logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
format_str = '%(levelname)s:%(lineno)s:%(message)s'
formatter = logging.Formatter(format_str)
ch.setFormatter(formatter)
logger.addHandler(ch)

class TreadmillWorkoutRecommendationType(enum.Enum):
    IPPT_SCORING_TABLE = 0
    VO2MAX = 1


## treadmill/spinning bike recommendation
def get_target_ave_met(user_id,
                       exercise_type,
                       recommendation_type = TreadmillWorkoutRecommendationType.IPPT_SCORING_TABLE):
    
    ## get age and MET history
    user = get_user_details(user_id)        
    if "user_dob" in user.keys():
        user_age = calculate_age(user['user_dob'])
        user_age_group = convertAgeToGroup(user_age)
    else: # defaults to easiest age range
        user_age_group = 14
    
    target_met_seconds = None

    if recommendation_type == TreadmillWorkoutRecommendationType.IPPT_SCORING_TABLE: 

        user_met_seconds = 0
        if "computed_met" in user.keys():
            for data in user['computed_met']['data']:
                if data['exercise_type'] == exercise_type:
                    user_met_seconds = data['max_total_met_seconds']      

        ## use MET lookup table
        target_table = pd.read_csv("routes/exercises/met-seconds_targets_table.csv", index_col=0)
        target_table = target_table.astype(int)
        target_table.columns = [int(i) for i in target_table.columns]
        
        (wo_lvl, target_met_seconds) = getMETperSecondWorkoutTarget(
                                    age_group=user_age_group,
                                    currentMetSeconds=user_met_seconds,
                                    target_table=target_table
                                    )
    elif recommendation_type == TreadmillWorkoutRecommendationType.VO2MAX:

        # Get Vo2Max and runTime_2_4
        vo2max = None
        time_2_4k = None
        if "fastest2.4km" in user.keys():
            for data in user['fastest2.4km']['data']:
                if data['exercise_type'] == exercise_type:
                    vo2max = data['max_2.4km_vo2max']  
                    time_2_4k = data['min_2.4km_sec']
        
        if vo2max == None or time_2_4k == None:
            raise Exception()

        target_met_seconds = vo2MaxRunIntensityRecommendation(
                                                        time_2_4=time_2_4k,
                                                        vo2max=vo2max,
                                                        user_age=user_age
                                                        )


    else:
        raise Exception("Invalid TreadmillWorkoutRecommendationType") 
        

    return {"recommended_metabolic_equivalent_seconds":int(target_met_seconds)}

#Treadmill Vo2Max based recommendation 



## weightstack recommendation
def get_target_one_rep_max(user_id, exercise_name, location):
    user = get_user_details(user_id)     

    user_1_RM = 0
    ## User 1RM
    ## TODO: segregate user 1RM by location
    if "computed_1_rep_max" in user.keys():
        for data in user['computed_1_rep_max']['data']:
            if data['exercise_name'] == exercise_name:
                user_1_RM = data['1_rep_max']      

    ## Default 1RM
    if not user_1_RM:
        # get ten-rep-first-quartile based on exercise_name and location
        trfq = get_ten_rep_first_quartile(exercise_name, location)
        if trfq:
            ## convert ten rep weight to 1RM using Brzycki equation
            # one_rep_max = weight * 36 / (37 - reps)
            user_1_RM = trfq * 36 / (37 - 10)
        else: 
            ## arbitrarily chosen
            user_1_RM = 10 
    
    ## Bump up 1RM by a certain multiplier (e.g. 5%)
    # recommended_one_rep_max = float(user_1_RM * 1.05)
    recommended_one_rep_max = float(user_1_RM)

    return {"recommended_one_rep_max": recommended_one_rep_max}


## bodyweight recommendation
def get_target_30s_max_rep(user_id, exercise_name):

    user = get_user_details(user_id)        
    if "user_dob" in user.keys():
        user_age = calculate_age(user['user_dob'])
        ageband = (math.ceil((user_age - 21) / 3 )) + 1
    else: # defaults to easiest age range
        ageband = 8
    logger.debug(f"user_id, ageband: {user_id, ageband}")

    if exercise_name == "pushup":
        #table to determine which tier the user is on based on 30SMR
        age_tsmr_to_tier = pd.read_csv("routes/exercises/age_tsmr_to_tier_pushup.csv")
        #table to determine how many reps to do in 30s based on tier
        age_tier_to_target = pd.read_csv("routes/exercises/age_tier_to_target_pushup.csv")
    if exercise_name == "situp":
        #table to determine which tier the user is on based on 30SMR
        age_tsmr_to_tier = pd.read_csv("routes/exercises/age_tsmr_to_tier_situp.csv")
        #table to determine how many reps to do in 30s based on tier
        age_tier_to_target = pd.read_csv("routes/exercises/age_tier_to_target_situp.csv")

    if "computed_30_sec_mr" in user.keys():
        for data in user['computed_30_sec_mr']['data']:
            if data['exercise_name'] == exercise_name:
                user_average30sMR = min(data['30_sec_mr'],30)
        tier = age_tsmr_to_tier.iloc[ageband,user_average30sMR]
    else: # defaults to easiest tier
        tier = 1
    target_tier = min(tier+1, 15)
    logger.debug(f"user_id, tier: {user_id, tier}")
    logger.debug(f"user_id, target_tier: {user_id, target_tier}")

    target_30s_max_rep = age_tier_to_target.iloc[ageband,target_tier]
    logger.debug(f"user_id, target_30s_max_rep: {user_id, target_30s_max_rep}")

    return {"recommended_thirty_sec_max_rep":int(target_30s_max_rep)}


def convertAgeToGroup(age: int) -> int:
    
    assert age >= 0, "Age must be greater than 0"
    
    if age < 22:    return 1
    elif age <=24:  return 2
    elif age <=27:  return 3
    elif age <=30:  return 4
    elif age <=33:  return 5
    elif age <=36:  return 6
    elif age <=39:  return 7
    elif age <=42:  return 8
    elif age <=45:  return 9
    elif age <=48:  return 10
    elif age <=51:  return 11
    elif age <=54:  return 12
    elif age <=57:  return 13
    else:           return 14


def getCurrentLvl(ageGroup: int, currentMetSeconds: float, target_table) -> int:
    '''
    Treadmill Run Workout recommendation based on IPPT scoring table - Helper function
    '''

    age_group_col_name = ageGroup
    diff = (currentMetSeconds - target_table[age_group_col_name])
    v = diff[diff >= 0] 
    if v[v >= 0].empty:
        return -1
    else:
        met_i = (v[v >= 0]).idxmin()
        return met_i 
    

def getMETperSecondWorkoutTarget(age_group: int,
                                 currentMetSeconds: float,
                                 target_table):

    '''
    Computes Treadmill Run Workout recommendation based on IPPT scoring table
    '''
    
    curr_met_i = getCurrentLvl(age_group, currentMetSeconds, target_table)
    
    print(f'Current lvl: {curr_met_i} with METsec: {currentMetSeconds}')
    
    if curr_met_i == 5:
        print("Max for current age lvl achieved")
        next_lvl = 5
        max_targets = target_table.iloc[5,:]
        
        diff = (currentMetSeconds - max_targets)        
        met_j = (diff[diff >= 0]).idxmin()
        print(f'current age group: {met_j}')
        if met_j == 1:
            print("MIN AGE GROUP MET CAN EVER REACH")
            met_v = target_table.loc[next_lvl, met_j]
        else:
            next_lvl = 5
            prev_age_group = met_j - 1
            met_v = target_table.loc[next_lvl, prev_age_group]

    else:
        next_lvl = curr_met_i + 1
        met_v = target_table.loc[next_lvl, age_group]
        
    print(f'recommended workout: {next_lvl} with METsec: {met_v}')
    
    return (next_lvl, met_v)


def calculate_age(born):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def get_user_details(user_id):
    query = {
        "_id": ObjectId(user_id),  # Match user
    }

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_users,
            # codec_options=options
        )
        cur = coll.find(query)
    cur_list = list(cur)

    return cur_list[0]

def get_latest_user_weight(user_id):
    '''Get latest user weight.
    Args:
        user_id (str): User id
    Returns:
        float: User weight
    '''
    # Construct query
    query = {
        "$match": {
            "user_id": user_id,  # Match user
            "exercise_name": "Weighing Scale",
        }
    }

    # Construct projection
    project = {
        "$project": {
            "_id": 0,
            "user_id": 1,
            "user_weight": "$weighing_scale_data.weight",  # Keep only weight
            "created": 1,  # Keep created date
        }
    }

    # Construct sort
    sort = {
        "$sort": {
            "created": pymongo.DESCENDING,  # Latest on top
        }
    }

    # Construct limit
    limit = {
        "$limit": 1,  # Keep top (i.e. most recent)
    }

    # Assemble pipeline
    pipeline = [
        query,
        project,
        sort,
        limit,
    ]

    # Actual query
    with MDB(mongo_ip, mongo_port, mongo_user, mongo_password) as conn:
        db = conn[db_gym]
        coll = db.get_collection(
            coll_bodymetrics,
            # codec_options=options
        )
        cur = coll.aggregate(pipeline)
        result = list(cur)

    # Non-empty list
    if result:
        return result[0]["user_weight"]
    # Empty list
    else:
        return 60