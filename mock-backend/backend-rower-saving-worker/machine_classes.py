import numpy as np
import pandas as pd
import logging

from pandas.core.base import SelectionMixin

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


class Exercise:
    def __init__(
        self,
        userid,
        nickname,
        gender,
        machineid,
        name,
        location,
        exercise,
        timeStarted,
        timeEnded,
        data,
        summary
    ):
        self.userid = userid
        self.nickname = nickname
        self.gender = gender
        self.machineid = machineid
        self.name = name
        self.location = location
        self.exercise = exercise
        self.timeStarted = timeStarted
        self.timeEnded = timeEnded
        self.data = data
        self.summary = summary

    def to_dict(self):

        return {
            'user_id': self.userid,
            'user_display_name': self.nickname,
            'user_gender': self.gender,
            'exercise_machine_id': self.machineid,
            'exercise_name': self.name,
            'exercise_location': self.location,
            'exercise_type': self.exercise,
            'exercise_started': int(self.timeStarted.timestamp() * 1000),
            'exercise_ended': int(self.timeEnded.timestamp() * 1000),
            'exercise_data': [ele.to_dict() for ele in self.data],
            'exercise_summary': self.summary,
        }


class ExerciseDetail:
    def __init__(self, machineId, userid, gender, nickname, name, location, exerciseType):
        self.machineId = machineId
        self.userid = userid
        self.gender = gender
        self.nickname = nickname
        self.name = name
        self.location = location
        self.exerciseType = exerciseType
        #self.user_gender = user_gender.lowercase()


class BodyMetrics:
    def __init__(
        self,
        userid,
        nickname,
        gender,
        machineId,
        name,
        location,
        timestamp,
        data,

    ):
        self.userid = userid
        self.nickname = nickname
        self.gender = gender
        self.machineId = machineId
        self.name = name
        self.location = location
        self.data = data
        self.timestamp = timestamp

    def to_dict(self):

        return {
            'user_id': self.userid,
            'user_nickname': self.nickname,
            'user_gender': self.gender,
            'machineId': self.machineId,
            'exercise_name': self.name,
            'exercise_location': self.location,
            'weighing_scale_data': self.data.toDict(),
            'timestamp': self.timestamp.timestamp() * 1000,
        }

class Rower:
    def __init__(self, distance, cadence, calories, strokes, timestamp, workoutTime, pace, power):
        self.distance = float(distance)
        self.cadence = float(cadence)
        self.calories = float(calories)
        self.strokes = float(strokes)
        self.timestamp = timestamp
        self.workoutTime = float(workoutTime)
        self.pace = float(pace)
        self.power = float(power)


    def to_dict(self):

        return {
            'distance': self.distance,
            'cadence': self.cadence,
            'calories': self.calories,
            'strokes': self.strokes,
            'timestamp': int(self.timestamp.timestamp() * 1000),
            'workoutTime': self.workoutTime,
            'pace': self.pace,
            'power': self.power
        }

