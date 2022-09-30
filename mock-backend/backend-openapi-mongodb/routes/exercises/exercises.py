from src import mongoapi2

from routes.exercises.exercises_helpers import * 
from flask import Response
from bson.json_util import dumps
import json

def get(
  username: str,
  sortDateBy: str,
  aggregateBy: str
):
  result = get_exercise(username,sortDateBy,aggregateBy)
  # print(result)

  result_json = dumps(result)
  if result:
    status_code = 200
  else:
    status_code = 404

  res = Response(
    response=result_json,
    status=status_code
  )

  return res

def get_recommendation(
  exercise_name: str,
  user_id: str,
  location: str = ''
):
  """Routes GET /exercises/exercise_name/{exercise_name}/users/{user_id}/recommendation

  Args:
    exercise_name: exercise name
    user_id: User ID
  Returns:
    dict
  """
  res = {}
  exercise_type = exercise_name_to_exercise_type(exercise_name)

  if exercise_type in ["treadmill","bike"]:
    res.update(get_target_ave_met(user_id, exercise_type))

  if exercise_type == "weightstack":
    res.update(get_target_one_rep_max(user_id, exercise_name, location))

  if exercise_type == "bodyweight":
    res.update(get_target_30s_max_rep(user_id, exercise_name))
  
  status_code = 200

  return res, status_code
  

def post(
  body: dict
):
  """Routes POST /exercises

  Args:
    user: Authenticated user
    body: Request body
  Returns:
    Nothing
  """
  # print('post', user, body, flush=True)

  result = post_exercise(body)

  if result.acknowledged:
    status_code = 201
  else:
    status_code = 500

  res = Response(
    response=json.dumps({"exercise_id": str(result.inserted_id)}),
    status=status_code
  )

  return res

def post_bodymetrics(
  body: dict
):
  """Routes POST /bodyMetrics

  Args:
    user: Authenticated user
    body: Request body
  Returns:
    Nothing
  """
  # print('post_bodymetrics', user, body, flush=True)

  result = post_bodymetrics_entry(body)

  if result:
    status_code = 201
  else:
    status_code = 500

  res = Response(
    response=None,
    status=status_code
  )

  return res

def get_insights_records(userId: str):
  # Route 
  result = mongoapi2.get_insights_records(userId)

  # Status
  if result:
      status_code = 200
  else:
      result = None
      status_code = 404

  return result, status_code

