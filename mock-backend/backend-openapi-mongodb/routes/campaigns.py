import datetime
import logging
from src import mongoapi2
from flask import Response

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


def get(active=None):
	'''Routes /campaigns
	Args:
		body: request body
	Returns:
		list: list of campaign objects
	'''
	result = mongoapi2.get_campaigns(active)

	if 'error' in result.keys():
		if 'Bad' in result['error']:
			status_code = 400
		elif 'Not found' in result['error']:
			status_code = 404
	else:
		status_code = 200
		result = result['res']

	return result, status_code
  
def post(body: dict):
	'''Routes /campaigns
	Args:
		body: request body
	Returns:
		nothing
	'''
	result = mongoapi2.post_campaign(body)

	if result:
		status_code = 201
	else:
		status_code = 500

	return result, status_code

def delete(campaignId: str):
	'''Routes /campaigns/{campaign_id}
	Args:
		campaignId: id of campaign
	Returns:
		Nothing
	'''
	result = mongoapi2.delete_campaign(campaignId)

	if 'error' in result.keys():
		if 'Bad' in result['error']:
			status_code = 400
		elif 'Not found' in result['error']:
			status_code = 404
	else:
		status_code = 200

	return result, status_code

def get_campaign_by_id(campaignId: str):
	'''Routes /campaigns/{campaign_id}
	Args:
		campaignId: id of campaign
	Returns:
		a campaign object
	'''
	result = mongoapi2.get_campaign_by_id(campaignId)

	if 'error' in result.keys():
		if 'Bad' in result['error']:
			status_code = 400
		elif 'Not found' in result['error']:
			status_code = 404
	else:
		status_code = 200

	return result, status_code

def get_user_campaign_status(campaignId: str, userId: str):
	'''Routes /campaigns/usercampaignstatus
	Args:
		campaignId: id of campaign
		userId: id of user
	Returns:
		a usercampaignstatus object
	'''
	result = mongoapi2.get_user_campaign_status(campaignId, userId)

	if 'error' in result.keys():
		if 'Bad' in result['error']:
			status_code = 400
		elif 'Not found' in result['error']:
			status_code = 404
	else:
		status_code = 200

	return result, status_code

def post_user_campaign_status(body: dict):
	'''Routes /campaigns/usercampaignstatus
	Args:
		body: request body
	Returns:
		nothing
	'''
	result = mongoapi2.post_user_campaign_status(body)

	if result:
		status_code = 201
	else:
		status_code = 500

	return result, status_code

def patch_user_campaign_status(campaignId: str, userId: str, body):
	'''Routes /campaigns/usercampaignstatus
	Args:
		campaignId: id of campaign
		userId: id of user
		newUserCampaignStatus: new usercampaignstatus object
	Returns:
		nothing
	'''
	result = mongoapi2.patch_user_campaign_status(campaignId, userId, body)

	if 'error' in result.keys():
		if 'Bad' in result['error']:
			status_code = 400
		elif 'Not found' in result['error']:
			status_code = 404
	else:
		status_code = 200

	return result, status_code

def calculateUserCampaignStatusV2(
    user_id: str,
    location: str,
    selector: str,
	):
    """Routes /campaigns/users/{user_id}/calculate-status

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
    result = mongoapi2.dispatch_campaign_calculation(user_id, location, selector)

    if result:
        status_code = 201
    else:
        status_code = 500

    return result, status_code

def calculateUserCampaignStatusV2ById(
    campaign_id: str,
    user_id: str
	):
    """Routes /campaigns/{campaign_id}/users/{user_id}/calculate_status

    Args:
        user: Authenticated user
		campaign_id: Requested campaign id
		user_id: Requested user id
    Returns:
        None
    """
	
    print(f"Processing campaign {campaign_id} for {user_id}")

    ## submit a task via postman-service
    result = mongoapi2.dispatch_campaign_calculation(user_id, "", campaign_id)

    if result:
        status_code = 201
    else:
        status_code = 500

    return result, status_code


def claimReward(
	user: str,
    campaign_id: str,
    user_id: str,
	reward_id: str,
	body:dict
	):
	"""Routes /campaigns/{campaign_id}/users/{user_id}/rewards/{reward_id}/claim
	Args:
	    user: Authenticated user
		campaign_id: Requested campaign id
		user_id: Requested user id,
		reward_id: ID of reward that user claimed
	Returns:
	    Updated user campaign status
	"""
	## update rewards table if reward_id and cumulative_challenge_id tally
	result, status_code = claimRewardById(
                            reward_id,
                            event_id=campaign_id, 
                            event_type='campaigns'
                            )
	if 'error' in result.keys():
            return result, status_code

	## update usercampaignstatus
	claim = {
		"claim_date": datetime.datetime.now(),
		"claim_rating": body['claim_rating'],
		"reward_id": reward_id
	}
	result = mongoapi2.patch_append_user_claims(campaign_id, user_id, claim)

	if 'error' in result.keys():
		if 'Bad' in result['error']:
			status_code = 400
		elif 'Not found' in result['error']:
			status_code = 404
		return result, status_code
	else:
		status_code = 200


	return result, status_code

	