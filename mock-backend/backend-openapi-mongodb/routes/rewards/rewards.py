from routes.rewards.reward_helpers import *

def getRandomReward(reward_selection_id: str):
	'''Routes /rewards/random/reward-selections/{reward_selection_id}
	Args:
		reward_selection_id: id of record in rewardselection collection in MongoDB
	Returns:
		a reward object
	'''
	result = get_random_reward(reward_selection_id)

	if 'error' in result.keys():
		if 'Bad' in result['error']:
			status_code = 400
		elif 'Not found' in result['error']:
			status_code = 404
	else:
		status_code = 200

	return result, status_code


def claimRewardById(reward_uuid: str, event_id=None, event_type=None):
	'''Routes /rewards/{reward_uuid}/claim
	Args:
		reward_uuid: id of reward in rewards table in Postgres
	Returns:
		updated_rows: no. of rows updated in rewards table
	'''
	result = decrement_reward_quantity(reward_uuid, event_id, event_type)

	if 'error' in result.keys():
		if 'Bad' in result['error']:
			status_code = 400
		elif 'Not found' in result['error']:
			status_code = 404
	else:
		status_code = 204

	return result, status_code