from src import mongoapi2
from flask import Response

def getAllWearableDetails(userId: str):
  """Routes /user/{userId}/wearables

  Args:
    userId: Requested user id
  Returns:
    wearable details
  """

  # It not found, {error: 'Not found'} returned
  result = mongoapi2.get_all_wearable_details(userId)
  return _gen_response(result, is_get=True)


def getAllWearableData(userId: str,
  dataType = None,
  startDate = None,
  endDate = None):
  """Routes /user/{userId}/wearables/data

  Args:
    userId: Requested user id
  Returns:
    all wearable data
  """

  # It not found, {error: 'Not found'} returned
  result = mongoapi2.get_all_wearable_data(userId, dataType, startDate, endDate)
  return _gen_response(result, is_get=True)

def getOneWearableDetails(userId: str, wearableId: str):
  """Routes /user/{userId}/wearables/{wearableId}

  Args:
    userId: Requested user id
  Returns:
    wearable details
  """
  # It not found, {error: 'Not found'} returned
  result = mongoapi2.get_one_wearable_details(userId, wearableId)
  return _gen_response(result, is_get=True)

def updateWearableDetails(
    body: dict
):
  """Routes POST /wearables

  Args:
    body: Request body
  Returns:
    Nothing
  """

  # returns res.acknowledged (write concern true/false)
  result = mongoapi2.update_wearable_details(body)
  return _gen_response(result, is_get=False)

def deleteWearableDetails(userId: str, wearableId: str):
  """Routes /users/{userId}/wearables/{wearableId}

    Args:
      userId: Requested user id
      wearableId: Requested wearable id
      body: request body
    Returns:
      success/ failure
    """

  result = mongoapi2.delete_wearable_details(userId=userId, wearableId=wearableId)

  return _gen_response(result, is_get=False)
  

def getWearableData(
  userId: str,
  wearableId: str,
  dataType = None,
  startDate = None,
  endDate = None
):
  """Routes /users/{userId}/wearables/{wearableId}/data

    Args:
      userId: Requested user id
      wearableId: Requested wearable id
      body: request body
    Returns:
      wearable data
    """
  result = mongoapi2.get_wearable_data(userId, wearableId, dataType, startDate, endDate)
  return _gen_response(result, is_get=True)
  

def updateWearableData(
  userId: str,
  wearableId: str,
  body: dict
):
  """Routes POST /users/{userId}/wearables/{wearableId}/data

  Args:
    userId: Requested user id
    body: Request body
  Returns:
    Nothing
  """
  result = mongoapi2.update_wearable_data(userId, wearableId, body)
  return _gen_response(result, is_get=False)

def getWearableAuthKey(
  wearableModel: str
):
  """
  Routes /wearable/{wearableModel}/authKey
    Args:
      wearableModel: str
    Returns:
      wearableAuthKey: str,
      status_code: int
  """
  key = wearableModel.upper() + '_AUTH_KEY'
  result = mongoapi2.get_wearable_auth_key(key)

  return _gen_response(result, is_get=True)

def _gen_response(result, is_get):
  # if is_get:
  #   if result:
  #     status_code = 200
  #   else:
  #     status_code = 404
  #     # result = None
  # else:
  #   if result:
  #     status_code = 200
      
  #     # result = None
  #   else:
  #     status_code = 500
  #     # result = None

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


