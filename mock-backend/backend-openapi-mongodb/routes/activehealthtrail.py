from src import mongoapi2
from flask import Response


# CHECKPOINT RELATED
# Update checkpoint details
def getAllCheckpointDetails():
  """Routes GET /activehealthtrail/get_all_checkpoint_details
    Args:
      checkpoint_id: checkpoint to be updated
      body: dictionary of neighboring checkpoint and the distance apart
    Returns:
      None  
  """

  result = mongoapi2.get_all_aht_checkpoint_details()
  return _gen_response(result, is_get=True)

def getOneCheckpointDetails(checkpointId : str):
  """Routes GET /activehealthtrail/{checkpointId}
    Args:
      checkpoint_id: checkpoint to be updated
      body: dictionary of neighboring checkpoint and the distance apart
    Returns:
      None  
  """

  result = mongoapi2.get_one_aht_checkpoint_details(checkpointId)
  return _gen_response(result, is_get=True)


def updateCheckpointDetails(body: dict):
  """Routes POST /activehealthtrail/update_checkpoint_details
    Args:
      checkpoint_id: checkpoint to be updated
      body: dictionary of neighboring checkpoint and the distance apart
    Returns:
      None  
  """

  result = mongoapi2.update_aht_checkpoint_details(body)
  return _gen_response(result, is_get=False)


# CHECK-IN RELATED
# Get user check-in details
def getAhtCheckinDetails(userId: str):
  """Routes GET /users/{userId}/activehealthtrail/checkins

  Args:
    userId: Requested user id
  Returns:
    user's checkin data
  """
  result = mongoapi2.get_aht_checkin_data(userId)
  return _gen_response(result, is_get=True)


# Post user check-in details
def updateAhtCheckinData(
  body: dict
):
  """Routes POST /activehealthtrail/update_checkin

  Args:
    body: Request body
  Returns:
    Nothing
  """
  result = mongoapi2.update_aht_checkin_data(body)
  return _gen_response(result, is_get=False)







def _gen_response(result, is_get):
  if is_get:
    try:
      return result['data'], result['status_code']

    except:
      return result['error'], result['status_code']
  
  else:
    if result:
      try:
        return result['success'], result['status_code']

      except:
        return result['error'], result['status_code']
    
    else:
      return None, 500


