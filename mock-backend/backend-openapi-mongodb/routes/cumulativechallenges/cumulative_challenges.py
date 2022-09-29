import logging
from datetime import datetime
import time
import json
from flask import Response

from routes.cumulativechallenges.cumulative_challenges_helpers import *
from routes.rewards.rewards import claimRewardById

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
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.ERROR)
ch = logging.StreamHandler()
format_str = '%(levelname)s:%(lineno)s:%(message)s'
formatter = logging.Formatter(format_str)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info('Logger ready')

# Set up logger
logger = logging.getLogger(__name__)
# logger.setLevel(logging.WARNING)
# logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.ERROR)
ch = logging.StreamHandler()
format_str = "%(levelname)s:%(lineno)s:%(message)s"
formatter = logging.Formatter(format_str)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info("Logger ready")


def get_cumulative_challenges(
    active: bool = None,
    location: str = "all"
    ):
    """Routes /cumulativechallenges

    Args:
      location: Requested gym location
      selector: "ongoing or latest"(default: all)
    Returns:
      cumulative_challenges base on filter in body [cumulative_challenge_id or location]
    """
    try:
        result = mongo_cumulative_challenges(location=location, active=active)
        return result, 200
    except:
        result = {}
        return result, 400


def get_cumulative_challenges_status(
    user_id: str, 
    cumulative_challenge_id: str
):
    """Routes /cumulative-challenges/{cumulative_challenge_id}/users/{user_id}/status
    
    Args:
      cumulative_challenge_id: Requested cumulative_challenge id
      user_id: Requested user id
    
    Returns:
      cumulative_challenges_status base on filter in body [cumulative_challenge_status_id or location]
    """
    try:
        result = mongo_cumulative_challenges_status(
            user_id=user_id,
            cumulative_challenge_id=cumulative_challenge_id,
        )
        return result, 200
    except:
        result = {}
        return result, 400


def calculateUserCumulativeChallengeStatus(
    user_id: str,
    location: str,
    selector: str,
    ):
    """Routes /cumulative-challenges/users/{user_id}/calculate-status

    Args:
        user: Authenticated user
        params:
            - user_id: Requested user id
            - location: Requested gym location
            - selector: "ongoing or latest"(default: ongoing)
    Returns:
        None
    """

    print(f"Processing {selector} campaign(s) in {location}")


    ## submit a task via postman-service
    result = dispatch_cumulative_challenge_calculation(
        user_id=user_id, location=location, target=selector
    )

    if result:
        status_code = 201
    else:
        status_code = 500

    return result, status_code


def calculateUserCumulativeChallengeStatusById(
    user: str, cumulative_challenge_id: str, user_id: str
):
    """Routes /cumulative_challenges/{cumulative_challenge_id}/users/{user_id}/calculate_status

    Args:
        user: Authenticated user
        cumulative_challenge_id: Requested cumulative_challenge id
        user_id: Requested user id
    Returns:
        None
    """

    print(f"Processing cumulative_challenge {cumulative_challenge_id} for {user_id}")

    ## submit a task via postman-service
    result = dispatch_cumulative_challenge_calculation(
        user_id, "", cumulative_challenge_id
    )

    if result:
        status_code = 201
    else:
        status_code = 500

    return result, status_code


def calculateUserCumulativeChallengeStatus(
    user: str,
    user_id: str,
    location: str,
    selector: str,
	):
    """Routes /cumulative-challenges/users/{user_id}/calculate-status

    Args:
        user: Authenticated user
        params:
            - user_id: Requested user id
            - location: Requested gym location
            - selector: "ongoing or latest"(default: ongoing)
    Returns:
        None
    """
	
    print(f"Processing {selector} campaign(s) in {location}")
	

    ## submit a task via postman-service
    result = dispatch_cumulative_challenge_calculation(user_id, location, selector)

    if result:
        status_code = 201
    else:
        status_code = 500

    return result, status_code

def calculateUserCumulativeChallengeStatusById(
    user: str,
    cumulative_challenge_id: str,
    user_id: str
	):
    """Routes /cumulative_challenges/{cumulative_challenge_id}/users/{user_id}/calculate_status

    Args:
        user: Authenticated user
        cumulative_challenge_id: Requested cumulative_challenge id
		user_id: Requested user id
    Returns:
        None
    """

    print(f"Processing cumulative_challenge {cumulative_challenge_id} for {user_id}")
	

    ## submit a task via postman-service
    result = dispatch_cumulative_challenge_calculation(user_id, "", cumulative_challenge_id)

    if result:
        status_code = 201
    else:
        status_code = 500

    return result, status_code

def claimReward(
	user: str,
    cumulative_challenge_id: str,
    user_id: str,
	reward_id: str,
	body:dict
	):
	"""Routes /cumulative-challenge/{cumulative_challenge_id}/users/{user_id}/rewards/{reward_id}/claim
	Args:
	    user: Authenticated user
		cumulative_challenge_id: Requested cumulative-challenge id
		user_id: Requested user id,
		reward_id: ID of reward that user claimed
	Returns:
	    Updated user cumulative-challenge status
	"""

    ## update rewards table if reward_id and cumulative_challenge_id tally
	result, status_code = claimRewardById(
                            reward_id,
                            event_id=cumulative_challenge_id, 
                            event_type='cumulative_challenges'
                            )
	if 'error' in result.keys():
            return result, status_code
		

	## update user_cumulative_challenge_status
	claim = {
		"claim_date": datetime.now(),
		"claim_rating": body['claim_rating'],
		"reward_id": reward_id
	}
	result = patch_append_user_claims(cumulative_challenge_id, user_id, claim)

	if 'error' in result.keys():
		if 'Bad' in result['error']:
			status_code = 400
		elif 'Not found' in result['error']:
			status_code = 404
		return result, status_code
	else:
		status_code = 200

	return result, status_code
