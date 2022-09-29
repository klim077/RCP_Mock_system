from src import mongoapi2
from flask import Response


def get(
    user: str,
    userId: str
):
    """Routes /users/{userId}

    Args:
      user: Authenticated user
      userId: Requested user id
    Returns:
      User information
    """

    print('get', flush=True)

    # Routing
    result = mongoapi2.get_user(user, userId)

    # Get keys
    keys = result.keys()

    # Make status
    if 'error' in keys:
        if 'Bad' in result['error']:
            status_code = 400
        if 'not found' in result['error']:
            status_code = 404
    else:
        status_code = 200

    # Prepare response
    # res = Response(
    #     response=result_json,
    #     status=status_code
    # )

    return result, status_code


def patch(
    user: str,
    userId: str,
    option: str,
    newValue: str,
):
    """Routes /users/{userId}

    Args:
      user: Authenticated user
      userId: Requested user id
      option: User information to change
      newValue: New value of information to change
    Returns:
      User information
    """

    print('update', flush=True)

    # Routing
    result = mongoapi2.update_user(user, userId, option, newValue)

    # Get keys
    keys = result.keys()

    # Make status
    if 'error' in keys:
        if 'Bad' in result['error']:
            status_code = 400
        elif 'not found' in result['error']:
            status_code = 404
        else:
            status_code = 401
    else:
        status_code = 200

    return result, status_code


def delete(
    user: str,
    userId: str
):
    """Routes /users/{userId}

    Args:
      user: Authenticated user
      userId: Requested user id
    Returns:
      User information
    """

    print('delete', flush=True)

    # Routing
    result = mongoapi2.delete_user(user, userId)

    # Get keys
    keys = result.keys()

    # Make status
    if 'error' in keys:
        if 'Bad' in result['error']:
            status_code = 400
        if 'not found' in result['error']:
            status_code = 404
    else:
        status_code = 200

    return result, status_code


def getUserExercises(
    user: str,
    userId: str,
    location='',
    start_date=0,
    end_date=0
):
    """Routes /users/{userId}/exercises

    Args:
      user: Authenticated user
      userId: Requested user id
      location: Location
      start_date: Start date
      end_date: End date
    Returns:
      List of exercise summaries filtered by query params
    """

    print('getUserExercises', flush=True)

    # Routing
    result = mongoapi2.get_user_exercises(user, userId, location=location, start_date=start_date, end_date=end_date)

    # Convert to json
    # result_json = dumps(result)

    # Make status
    if 'error' in result.keys():
        if 'Bad' in result['error']:
            status_code = 400
        elif 'Not found' in result['error']:
            status_code = 404
    else:
        status_code = 200
        result = result['res']

    # Prepare response
    # res = Response(
    #     response=result_json,
    #     status=status_code
    # )

    return result, status_code


def calculateUserCampaignStatus(
    user: str,
    userId: str
):
    """Routes /users/{userId}/calculateUserCampaignStatus

    Args:
      userId: Requested user id
    Returns:
      return user campaign status
    """

    print('calculateUserCampaignStatus', flush=True)

    # Routing
    result = mongoapi2.calculateUserCampaignStatus(user, userId)

    # Convert to json
    # result_json = dumps(result)

    # Make status
    if result:
        status_code = 200
    else:
        status_code = 404

    # Prepare response
    # res = Response(
    #     response=result_json,
    #     status=status_code
    # )

    return result, status_code


def getUserExerciseDetail(
    user: str,
    userId: str,
    exerciseId: str
):
    """ Routes /users/{userId}/exercises/{exerciseId}

    Args:
      user: Authenticated user
      userId: Requested user id
      exerciseId: Exercise Id
      Returns:
      Exercise detail
      """

    print('getUserExerciseDetail', flush=True)

    # Routing
    result = mongoapi2.get_user_exercise_detail(user, userId, exerciseId)

    # Convert to json
    # result_json = dumps(result)

    # Get keys
    keys = result.keys()

    # Make status
    # if result:
    #   status_code = 200
    # else:
    #   status_code = 404
    status_code = 200
    if 'error' in keys:
        if 'Bad' in result['error']:
            status_code = 400
        if 'not found' in result['error']:
            status_code = 404

    # Prepare response
    # res = Response(
    #     response=result_json,
    #     status=status_code
    # )

    return result, status_code


def updateCampaignClaims(
    user: str,
    userId: str,
    body: dict,
):
    """Routes /users/{userId}

    Args:
      user: Authenticated user
      userId: Requested user id
      body: User claims to update

    Returns:
      User information
    """

    # print(body)
    result = {
        'oritpass': '123123'
    }

    status_code = 200

    print('updateCampaignClaims', flush=True)

    # Routing
    result = mongoapi2.update_user_claims(user, userId, 'user_claims', body)

    # Get keys
    keys = result.keys()

    # Make status
    if 'error' in keys:
        if 'Bad' in result['error']:
            status_code = 400
        elif 'not found' in result['error']:
            status_code = 404
        else:
            status_code = 401
    else:
        status_code = 200

    return result, status_code

def get_user_records(userId:str,  exercise_name='',):

    """Routes /users/{userId}/records

    Args:
      userId: Requested user id

    Returns:
      User's records such as MET values and 1RM values
    """
    # Routing
    result = mongoapi2.get_user_records(userId,exercise_name )

    #Status
    if result:
      status_code = 200
    else:
      status_code = 404
    status_code = 200

    return result, status_code
