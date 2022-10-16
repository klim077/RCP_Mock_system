# from flask import Response
# from bson.json_util import dumps
from numpy.core.arrayprint import str_format
from src import mongoapi2
from common.redis import *

# from src.utils import makeResponse

import re

import logging
import time
import json

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
logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.ERROR)
ch = logging.StreamHandler()
format_str = "%(levelname)s:%(lineno)s:%(message)s"
formatter = logging.Formatter(format_str)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info("Logger ready")


def j(*args):
    return ":".join([str(ele) for ele in args])


def get_machines():
    """Routes /machines

    Args:
      user: Authenticated user
    Returns:
      list: List of machine id
    """
    logger.debug(f"Step into get_machines()")

    # Routing
    result = mongoapi2.get_machines()

    # Make status
    status_code = 200

    return result, status_code


def get_location():
    """Routes /machines/location

    Args:
      user: Authenticated user
    Returns:
      list: List of locations
    """
    logger.debug(f"Step into get_location()")

    # Routing
    result = mongoapi2.get_location()

    # Make status
    status_code = 200

    return result, status_code


def get_machines_by_location(location: str):
    """Routes /machines/location/{location}

    Args:
      user: Authenticated user
    Returns:
      list: List of machine id
    """
    logger.debug(f"Step into get_machines_by_location()")

    # Routing
    result = mongoapi2.get_machines_by_location(location)

    # Make status
    status_code = 200

    return result, status_code

def get_machine_info_by_id(machine_id:str):
    """Routes /machines/{machine_id}/info

    Args:
      machine_id: Machine UUID
    Returns:a
      list: Dict of machine metadata
    """
    logger.debug(f"Step into get_machine_info_by_id()")

    # Routing
    result = mongoapi2.get_machine_info_by_id(machine_id)

    # Make status
    status_code = 200

    return result, status_code


def xadd(machineId: str, key: str, body: dict):
    """Routes /machines/{machineId}/keyvalues/{key}/xadd

    Args:
      user: Authenticated user
      machineId: Machine id
      key: Name of key
      body: Dict to add
    Returns:
      Nothing
    """
    logger.debug(f"Step into xadd()")

    # Routing
    result = mongoapi2.xadd(machineId, key, body)

    # Make status
    if result:
        result = {}
        status_code = 201
    else:
        result = {}
        status_code = 400

    return result, status_code


def increment_key(machineId: str, key: str, body: dict):
    """Routes /machines/{machineId}/keyvalues/{key}/increment

    Args:
      user: Authenticated user
      machineId: Machine id
      key: Name of key
      body: Dict with a single key named [value]
    Returns:
      Nothing
    """

    logger.debug(f"Step into increment_key()")

    # Validate body
    if not body:
        body = {"value": 1.0}

    # Validate type
    error_msg = {"Error": "Value type error"}
    error_code = 400
    value = body["value"]
    logger.debug(f"{value} is type {type(value)}")
    if key == "reps" and not value.is_integer():
        return error_msg, error_code
    if key == "met_sum" and not isinstance(value, float):
        return error_msg, error_code
    if key == "calories" and not isinstance(value, float):
        return error_msg, error_code
    if key == "distance" and not isinstance(value, float):
        return error_msg, error_code
    if key == "workoutTime" and not isinstance(value, float):
        return error_msg, error_code
    if key == "altitude" and not isinstance(value, float):
        return error_msg, error_code
    if key == "total_speed" and not isinstance(value, float):
        return error_msg, error_code
    if key == "total_cadence" and not isinstance(value, float):
        return error_msg, error_code
    if key == "pedal" and not isinstance(value, float):
        return error_msg, error_code

    # Routing
    result = mongoapi2.increment_key(machineId, key, body)

    # Make status
    if result:
        result = {}
        status_code = 201
    else:
        result = {}
        status_code = 400

    return result, status_code


def initialize_rower_with_user(machineId: str, body: dict):
    """Routes /machines/{machineId}/initializeRowerWithUser

     Args:
      user: Authenticated user
      machineId: Machine id
      body: Dict with a single key named [value]
    Returns:
      Nothing
    """
    user = body["value"]

    result = mongoapi2.get_machines()

    for machine in result:
        machineDetails = mongoapi2.get_keyvalues(machine["uuid"])
        if machineDetails["user"] == user:
            logger.debug("got repeat the user")
            del_key(machine["uuid"], "user")

    logger.debug(
        f"Step into initialize_treadmill_with_user({machineId}, {body})"
    )

    # Routing
    r1 = del_key(machineId, "user")
    r2 = set_key(machineId, "user", body)
    r3 = set_key(machineId, "rec", {"value": "False"})
    r4 = set_key(machineId, "distance", {"value": 0.0})
    r5 = set_key(machineId, "cadence", {"value": 0.0})
    r6 = set_key(machineId, "calories", {"value": 0.0})
    r7 = set_key(machineId, "strokes", {"value": 0.0})
    r8 = set_key(machineId, "timestamp", {"value": 0.0})
    r9 = set_key(machineId, "workoutTime", {"value": 0.0})
    r10 = set_key(machineId, "pace", {"value": 0.0})
    r11 = set_key(machineId, "power", {"value": 0.0})
    r12 = set_key(machineId, "rowingTime", {"value": 0.0})
    r13 = set_key(machineId, "heartRate", {"value": 0.0})
    r14 = set_key(machineId, "interval", {"value": 0.0})
    r15 = del_key(machineId, "data_stream")
    r16 = set_key(machineId, "type", {"value": "rower"})
    #r_met_sum = set_key(user, machineId, "met_sum", {"value": 0.0})
    #r_met_instant = set_key(user, machineId, "met_instant", {"value": 0.0})

    # logger.debug(str(r1[1]) + " " + str(r2[1]) + " " + str(r3[1]) + " " + str(r4[1]) + " " + str(r5[1]) + " " + str(r6[1]))
    # logger.debug(str(r7[1]) + " " + str(r8[1]) + " " + str(r9[1]) + " " + str(r10[1]) + " " + str(r11[1]) + " " + str(r12[1]))
    # Make status
    if (
        (r1[1] == 201)
        & (r2[1] == 201)
        & (r3[1] == 201)
        & (r4[1] == 201)
        & (r5[1] == 201)
        & (r6[1] == 201)
        & (r7[1] == 201)
        & (r8[1] == 201)
        & (r9[1] == 201)
        & (r10[1] == 201)
        & (r11[1] == 201)
        & (r12[1] == 201)
        & (r13[1] == 201)
        & (r14[1] == 201)
        & (r15[1] == 201)
        & (r16[1] == 201)
        #& (r_met_sum[1] == 201)
        #& (r_met_instant[1] == 201)
    ):
        result = {}
        status_code = 201
    else:
        result = {}
        status_code = 400

    return result, status_code


# from gateway
# def spinnerUpdateRedis(user: str, machineId: str, body: dict):
#     """Routes /machines/{machineId}/spinnerUpdateRedis

#      Args:
#       user: Authenticated user
#       machineId: Machine id
#       body: Dict with a single key named [value]
#     Returns:
#       Nothing
#     """

#     # uses machine to set key and stuff
#     logger.info(f"SpinnerUpdateRedis()")

#     # Routing
#     try:

#         r1 = increment_key(user, machineId, "distance", {"value": body["distance"]})
#         r2 = increment_key(
#             user, machineId, "workoutTime", {"value": body["workoutTime"]}
#         )
#         r3 = increment_key(user, machineId, "calories", {"value": body["calories"]})
#         r4 = set_key(user, machineId, "power", {"value": body["power"]})
#         r5 = set_key(user, machineId, "speed", {"value": body["speed"]})
#         r6 = set_key(user, machineId, "cadence", {"value": body["cadence"]})
#         r7 = increment_key(
#             user, machineId, "total_speed", {"value": body["total_speed"]}
#         )
#         r8 = increment_key(
#             user, machineId, "total_cadence", {"value": body["total_cadence"]}
#         )
#         r9 = increment_key(user, machineId, "pedal", {"value": body["pedal"]})
#         r10 = set_key(user, machineId, "rec", {"value": body["rec"]})

#     except Exception as e:
#         logger.error(f'Spinner", {e}')

#     # to change back to debug
#     logger.info(
#         "SpinnerUpdateRedis"
#         + str(r1[1])
#         + " "
#         + str(r2[1])
#         + " "
#         + str(r3[1])
#         + " "
#         + str(r4[1])
#         + " "
#         + str(r5[1])
#         + " "
#         + str(r6[1])
#         + " "
#         + str(r7[1])
#         + " "
#         + str(r8[1])
#         + " "
#         + str(r9[1])
#         + " "
#         + str(r10[1])
#         + " "
#     )

#     # Make status
#     if (
#         (r1[1] == 201)
#         & (r2[1] == 201)
#         & (r3[1] == 201)
#         & (r4[1] == 201)
#         & (r5[1] == 201)
#         & (r6[1] == 201)
#         & (r7[1] == 201)
#         & (r8[1] == 201)
#         & (r9[1] == 201)
#         & (r10[1] == 201)
#     ):
#         result = {}
#         status_code = 201
#         mongoapi2.dispatch_bike_worker(machineId)

#     else:
#         result = {}
#         status_code = 400

#     return result, status_code


# def spinnerUpdateRedisFromPostman(user: str, machineId: str, body: dict):
#     """Routes /machines/{machineId}/spinnerUpdateRedisFromPostman

#      Args:
#       user: Authenticated user
#       machineId: Machine id
#       body: Dict with a single key named [value]
#       call a postman to save spinning bike data
#     Returns:
#       Nothing
#     """
#     # uses machine to set key and stuff

#     logger.debug(f"spinnerUpdateRedisFromPostman")
#     print(f"spinnerUpdateRedisFromPostman")

#     # Routing
#     try:

#         r1 = set_key(user, machineId, "distance", {"value": body["distance"]})
#         r2 = set_key(user, machineId, "workoutTime", {"value": body["workoutTime"]})
#         r3 = set_key(user, machineId, "calories", {"value": body["calories"]})
#         r4 = set_key(user, machineId, "power", {"value": body["power"]})
#         r5 = set_key(user, machineId, "speed", {"value": body["speed"]})
#         r6 = set_key(user, machineId, "cadence", {"value": body["cadence"]})
#         r7 = set_key(user, machineId, "avgSpeed", {"value": body["avgSpeed"]})
#         r8 = set_key(user, machineId, "avgCadence", {"value": body["avgCadence"]})
#         r9 = set_key(user, machineId, "rec", {"value": body["rec"]})

#         data = {
#             "distance": body["distance"],
#             "workoutTime": body["workoutTime"],
#             "calories": body["calories"],
#             "power": body["power"],
#             "speed": body["speed"],
#             "cadence": body["cadence"],
#             "avgSpeed": body["avgSpeed"],
#             "avgCadence": body["avgCadence"],
#             "rec": body["rec"],
#             "timestamp": time.time(),
#         }

#         # print(f'data: {data}')

#         # add to stream for socketio to pick up
#         r10 = xadd(user, machineId, "data_stream", data)

#         print(f"Spinner r10({r10[1]})")

#     except Exception as e:
#         logger.error(f'spinnerUpdateRedisFromPostman", {e}')
#         print(f'spinnerUpdateRedisFromPostman", {e}')

#     # to change back to debug
#     logger.info(
#         "Spinning Bike postman update redis"
#         + str(r1[1])
#         + " "
#         + str(r2[1])
#         + " "
#         + str(r3[1])
#         + " "
#         + str(r4[1])
#         + " "
#         + str(r5[1])
#         + " "
#         + str(r6[1])
#         + " "
#         + str(r7[1])
#         + " "
#         + str(r8[1])
#         + " "
#         + str(r9[1])
#         + " "
#         + str(r10[1])
#         + " "
#     )

#     print(
#         "Spinning Bike postman update redis"
#         + str(r1[1])
#         + " "
#         + str(r2[1])
#         + " "
#         + str(r3[1])
#         + " "
#         + str(r4[1])
#         + " "
#         + str(r5[1])
#         + " "
#         + str(r6[1])
#         + " "
#         + str(r7[1])
#         + " "
#         + str(r8[1])
#         + " "
#         + str(r9[1])
#         + " "
#         + str(r10[1])
#         + " "
#     )

#     # Make status
#     if (
#         (r1[1] == 201)
#         & (r2[1] == 201)
#         & (r3[1] == 201)
#         & (r4[1] == 201)
#         & (r5[1] == 201)
#         & (r6[1] == 201)
#         & (r7[1] == 201)
#         & (r8[1] == 201)
#         & (r9[1] == 201)
#         & (r10[1] == 201)
#     ):
#         result = {}
#         status_code = 201
#         print(f"result: {result}")
#         print(f"status_code: {status_code}")

#     else:
#         result = {}
#         status_code = 400
#         print(f"else result: {result}")
#         print(f"else status_code: {status_code}")

#     return result, status_code
#     pass


def rowerUpdateRedis(machineId: str, body: dict):
    """Routes /machines/{machineId}/rowerUpdateRedis

     Args:
      user: Authenticated user
      machineId: Machine id
      body: Dict with a single key named [value]
    Returns:
      Nothing
    """

    logger.debug(f"RowerUpdateRedis()")

    # Routing
    try:
        r1 = set_key(
            machineId,
            "distance",
            {
                "value": body["distance"],
            },
        )
        logger.debug(f"Rower r1({r1[1]})")

        r2 = set_key(
            machineId,
            "cadence",
            {
                "value": body["cadence"],
            },
        )
        logger.debug(f"Rower r2({r2[1]})")

        r3 = set_key(
            machineId,
            "calories",
            {
                "value": body["calories"],
            },
        )
        logger.debug(f"Rower r3({r3[1]})")

        r4 = set_key(
            machineId,
            "strokes",
            {
                "value": body["strokes"],
            },
        )
        logger.debug(f"Rower r4({r4[1]})")

        r5 = set_key(
            machineId,
            "timestamp",
            {
                "value": body["timestamp"],
            },
        )
        logger.debug(f"Rower r5({r5[1]})")

        r6 = set_key(
            machineId,
            "workoutTime",
            {
                "value": body["workoutTime"],
            },
        )
        logger.debug(f"Rower r6({r6[1]})")

        r7 = set_key(
            machineId,
            "pace",
            {
                "value": body["pace"],
            },
        )
        logger.debug(f"Rower r7({r7[1]})")

        r8 = set_key(
            machineId,
            "power",
            {
                "value": body["power"],
            },
        )
        logger.debug(f"Rower r8({r8[1]})")

        r9 = set_key(
            machineId,
            "rowingTime",
            {
                "value": body["rowingTime"],
            },
        )
        logger.debug(f"Rower r9({r9[1]})")

        r10 = set_key(
            machineId,
            "heartRate",
            {
                "value": body["heartRate"],
            },
        )
        logger.debug(f"Rower r10({r10[1]})")

        r11 = set_key(
            machineId,
            "interval",
            {
                "value": body["interval"],
            },
        )
        logger.debug(f"Rower r11({r11[1]})")

        r12 = set_key(
            machineId,
            "rec",
            {
                "value": body["rec"],
            },
        )
        logger.debug(f"Rower r12({r12[1]})")

        # # Increment MET sum
        # r_met_sum = increment_key(
        #     user,
        #     machineId,
        #     "met_sum",
        #     {
        #         "value": body["met"],
        #     },
        # )
        # logger.debug(f"Treadmill r_met_sum({r_met_sum[1]})")

        # # Store instantaneous MET
        # r_met_instant = set_key(
        #     user,
        #     machineId,
        #     "met_instant",
        #     {
        #         "value": body["met"],
        #     },
        # )
        # logger.debug(f"Treadmill r_met_instant({r_met_instant[1]})")


        data = {
            "distance": body["distance"],
            "cadence": body["cadence"],
            "calories": body["calories"],
            "strokes": body["strokes"],
            "timestamp": time.time(),
            "workoutTime": body["workoutTime"],
            "pace": body["pace"],
            "power": body["power"],
            "rowingTime": body["rowingTime"],
            "heartRate": body["heartRate"],
            "interval": body["interval"],
            "rec": body["rec"],
            # "met": body["met"],
        }

        # r13 = xadd(
        #     machineId,
        #     "data_stream",
        #     data,
        # )
        # logger.debug(f"Rower r13({r13[1]})")

    except Exception as e:
        logger.error(f'Rower", {e}')

    logger.debug(
        "RowerUpdateRedis"
        + str(r1[1])
        + " "
        + str(r2[1])
        + " "
        + str(r3[1])
        + " "
        + str(r4[1])
        + " "
        + str(r5[1])
        + " "
        + str(r6[1])
        + " "
        + str(r7[1])
        + " "
        + str(r8[1])
        + " "
        + str(r9[1])
        + " "
        + str(r10[1])
        + " "
        + str(r11[1])
        + " "
        + str(r12[1])
        + " "
        # + str(r13[1])
        # + " "
        # + str(r_met_sum[1])
        # + " "
        # + str(r_met_instant[1])
    )
    # Make status
    if (
        (r1[1] == 201)
        & (r2[1] == 201)
        & (r3[1] == 201)
        & (r4[1] == 201)
        & (r5[1] == 201)
        & (r6[1] == 201)
        & (r7[1] == 201)
        & (r8[1] == 201)
        & (r9[1] == 201)
        & (r10[1] == 201)
        & (r11[1] == 201)
        & (r12[1] == 201)
        # & (r_met_sum[1] == 201)
        # & (r_met_instant[1] == 201)
    ):
        result = {}
        status_code = 201
        mongoapi2.dispatch_rower(machineId)
    else:
        result = {}
        status_code = 400

    return result, status_code


def rowerUpdateRedisFromPostman(machineId: str, body: dict):
    """Routes /machines/{machineId}/rowerUpdateRedisFromPostman

     Args:
      user: Authenticated user
      machineId: Machine id
      body: Dict with a single key named [value]
      call a postman to save rower data
    Returns:
      Nothing
    """
    # uses machine to set key and stuff

    logger.debug(f"rowerUpdateRedisFromPostman")
    print(f"rowerUpdateRedisFromPostman")

    # Routing
    try:

        r1 = set_key(machineId, "distance", {"value": body["distance"]})
        r2 = set_key(machineId, "cadence", {"value": body["cadence"]})
        r3 = set_key(machineId, "calories", {"value": body["calories"]})
        r4 = set_key(machineId, "strokes", {"value": body["strokes"]})
        r5 = set_key(machineId, "timestamp", {"value": body["timestamp"]})
        r6 = set_key(machineId, "workoutTime", {"value": body["workoutTime"]})
        r7 = set_key(machineId, "pace", {"value": body["pace"]})
        r8 = set_key(machineId, "power", {"value": body["power"]})
        r9 = set_key(machineId, "rowingTime", {"value": body["rowingTime"]})
        r10 = set_key(machineId, "heartRate", {"value": body["heartRate"]})
        r11 = set_key(machineId, "interval", {"value": body["interval"]})
        r12 = set_key(machineId, "rec", {"value": body["rec"]})

        data = {
            "distance": body["distance"],
            "cadence": body["cadence"],
            "calories": body["calories"],
            "strokes": body["strokes"],
            # "timestamp": time.time(),
            "timestamp": body["timestamp"],
            "workoutTime": body["workoutTime"],
            "pace": body["pace"],
            "power": body["power"],
            "rowingTime": body["rowingTime"],
            "heartRate": body["heartRate"],
            "interval": body["interval"],
            "rec": body["rec"],
            
        }

        # print(f'data: {data}')

        # add to stream for socketio to pick up
        r13 = xadd(machineId, "data_stream", data)

        print(f"Rower r13({r13[1]})")

    except Exception as e:
        logger.error(f'rowerUpdateRedisFromPostman", {e}')
        print(f'rowerUpdateRedisFromPostman", {e}')

    # to change back to debug
    logger.info(
        "Rower postman update redis"
        + str(r1[1])
        + " "
        + str(r2[1])
        + " "
        + str(r3[1])
        + " "
        + str(r4[1])
        + " "
        + str(r5[1])
        + " "
        + str(r6[1])
        + " "
        + str(r7[1])
        + " "
        + str(r8[1])
        + " "
        + str(r9[1])
        + " "
        + str(r10[1])
        + " "
        + str(r11[1])
        + " "
        + str(r12[1])
        + " "
        + str(r13[1])
        + " "
    )

    print(
        "Rower postman update redis"
        + str(r1[1])
        + " "
        + str(r2[1])
        + " "
        + str(r3[1])
        + " "
        + str(r4[1])
        + " "
        + str(r5[1])
        + " "
        + str(r6[1])
        + " "
        + str(r7[1])
        + " "
        + str(r8[1])
        + " "
        + str(r9[1])
        + " "
        + str(r10[1])
        + " "
        + str(r11[1])
        + " "
        + str(r12[1])
        + " "
        + str(r13[1])
        + " "
    )

    # Make status
    if (
        (r1[1] == 201)
        & (r2[1] == 201)
        & (r3[1] == 201)
        & (r4[1] == 201)
        & (r5[1] == 201)
        & (r6[1] == 201)
        & (r7[1] == 201)
        & (r8[1] == 201)
        & (r9[1] == 201)
        & (r10[1] == 201)
        & (r11[1] == 201)
        & (r12[1] == 201)
        & (r13[1] == 201)
    ):
        result = {}
        status_code = 201
        print(f"result: {result}")
        print(f"status_code: {status_code}")

    else:
        result = {}
        status_code = 400
        print(f"else result: {result}")
        print(f"else status_code: {status_code}")

    return result, status_code
    pass


def set_key(machineId: str, key: str, body: dict):
    """Routes /machines/{machineId}/keyvalues/{key}

    Args:
      user: Authenticated user
      machineId: Machine id
      key: Name of key
      body: Dict with a single key named [value]
    Returns:
      Nothing
    """

    logger.debug(f"Step into set_key()")

    # Validate type
    error_msg = {"Error": "Value type error"}
    error_code = 400
    value = body["value"]
    logger.debug(f"{value} is type {type(value)}")
    if key == "reps" and not isinstance(value, int):
        return error_msg, error_code
    if key == "weight" and not (isinstance(value, int) or isinstance(value, float)):
        return error_msg, error_code
    if key == "available" and not isinstance(value, int):
        return error_msg, error_code
    if key == "rec" and not isinstance(value, str):
        return error_msg, error_code
    if key == "user" and not isinstance(value, str):
        return error_msg, error_code
    if key == "avgCadence" and not isinstance(value, float):
        return error_msg, error_code
    if key == "avgSpeed" and not isinstance(value, float):
        return error_msg, error_code
    if key == "cadence" and not isinstance(value, float):
        return error_msg, error_code
    if key == "power" and not isinstance(value, float):
        return error_msg, error_code
    if key == "speed" and not isinstance(value, float):
        return error_msg, error_code
    if key == "met_sum" and not isinstance(value, float):
        return error_msg, error_code
    if key == "met_instant" and not isinstance(value, float):
        return error_msg, error_code
    if key == "calories" and not isinstance(value, float):
        return error_msg, error_code
    if key == "distance" and not isinstance(value, float):
        return error_msg, error_code
    if key == "workoutTime" and not isinstance(value, float):
        return error_msg, error_code
    if key == "altitude" and not isinstance(value, float):
        return error_msg, error_code
    if key == "inclination" and not isinstance(value, float):
        return error_msg, error_code
    if key == "is_ippt" and not isinstance(value, str):
        return error_msg, error_code
    if key == "exercise_group" and not isinstance(value, str):
        return error_msg, error_code
    if key == "exercise_name" and not isinstance(value, str):
        return error_msg, error_code
    if key == "bodylandmarks" and not isinstance(value, str):
        return error_msg, error_code
    if key == "timestamp" and not isinstance(value, float):
        return error_msg, error_code
    if key == "strokes" and not isinstance(value, float):
        return error_msg, error_code
    if key == "pace" and not isinstance(value, float):
        return error_msg, error_code
    if key == "pace" and not isinstance(value, float):
        return error_msg, error_code
    if key == "rowingTime" and not isinstance(value, float):
        return error_msg, error_code
    if key == "heartRate" and not isinstance(value, float):
        return error_msg, error_code
    if key == "interval" and not isinstance(value, float):
        return error_msg, error_code

    # Routing
    result = mongoapi2.set_key(machineId, key, body)

    # Make status
    if result:
        result = {}
        status_code = 201
    else:
        result = {}
        status_code = 400

    return result, status_code


def del_key(machineId: str, key: str):
    """Routes /machines/{machineId}/keyvalues/{key}

    Args:
      user: Authenticated user
      machineId: Machine id
      key: Name of key
    Returns:
      Nothing
    """

    logger.debug(f"Step into del_key()")

    # Validate type
    error_msg = {"Error": "Value type error"}
    error_code = 400
    accepted_strings = {"data_stream", "user"}

    if key not in accepted_strings:
        return error_msg, error_code

    # Routing
    result = mongoapi2.del_key(machineId, key)

    # Make status
    if result:
        result = {}
        status_code = 201
    else:
        result = {}
        status_code = 400

    return result, status_code


def get_keyvalues(machineId: str):
    """Routes /machines/{machineId}/keyvalues

    Args:
      user: Authenticated user
      machineId: Machine id
    Returns:
      Dict containing key-value pairs
    """

    logger.debug(f"Step into get_keyvalues()")

    # Routing
    result = mongoapi2.get_keyvalues(machineId)

    # Make status
    status_code = 200

    return result, status_code


def dispatch(machineId: str):
    """Routes /machines/{machineId}/dispatch

    Args:
      user: Authenticated user
      machineId: Requested machine id
    Returns:
      Nothing
    """

    logger.debug(f"Step into dispatch()")

    # Validate input
    # 32 characters within [a-zA-Z0-9_]
    pattern = "^\w{32}$"
    pattern_check = re.match(pattern, machineId)

    if not pattern_check:
        msg = f"Bad request: {machineId}"
        # logger.info(msg)
        return {"error": msg}, 400

    # Routing
    result = mongoapi2.dispatch_machine(machineId)  # num of subscribers

    if "Bad request" in result:
        # logger.info(f'Bad request: {machineId}')
        return {"error": result}, 400

    # Make status
    status_code = 202

    return result, status_code

