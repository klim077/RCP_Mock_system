from datetime import time
import numpy as np
from common import logger
from rower.model import ParameterQueue

class RowerWorkout:
    def __init__(
        self,
        distance,
        cadence,
        calories,
        strokes,
        timestamp,
        workoutTime,
        pace,
        power,
        rowingTime,
        heartRate,
        interval,
        rec,
        isEdge,
    ):

        self.distance = distance
        self.cadence = cadence
        self.calories = calories
        self.strokes = strokes
        self.timestamp = timestamp
        self.workoutTime = workoutTime
        self.pace = pace
        self.power = power
        self.rowingTime = rowingTime
        self.heartRate = heartRate
        self.interval = interval
        self.rec = rec
        self.isEdge = isEdge


    def to_dict(self):

        return{
            "distance": self.distance,
            "cadence": self.cadence,
            "calories": self.calories,
            "strokes": self.strokes,
            "timestamp": self.timestamp,       
            "workoutTime": self.workoutTime,
            "pace": self.pace,
            "power": self.power,
            "rowingTime": self.rowingTime,
            "heartRate": self.heartRate,
            "interval": self.interval,
            "rec": self.rec,
            "isEdge": self.isEdge,
        }

class WorkoutProcessor:

    def __init__(self):
        pass

    def rowerCompute(self, channelData):

        self.redis_dict = channelData

        self.distance =      float(self.redis_dict["distance"])
        self.cadence =       float(self.redis_dict["cadence"])
        self.calories =      float(self.redis_dict["calories"])
        self.strokes =       float(self.redis_dict["strokes"])
        self.timestamp =     float(self.redis_dict["timestamp"])
        self.workoutTime =   float(self.redis_dict["workoutTime"])
        self.pace =          float(self.redis_dict["pace"])
        self.power =         float(self.redis_dict["power"])
        self.rowingTime =    float(self.redis_dict["rowingTime"])
        self.heartRate =     float(self.redis_dict["heartRate"])
        self.interval =      float(self.redis_dict["interval"])
        self.rec =           self.redis_dict["rec"]
        self.isEdge =        float(self.redis_dict["isEdge"])

        print(f'distance: {self.distance}')
        print(f'cadence: {self.cadence}')
        print(f'calories: {self.calories}')
        print(f'strokes: {self.strokes}')
        print(f'timestamp: {self.timestamp}')
        print(f'workoutTime: {self.workoutTime}')
        print(f'pace: {self.pace}')
        print(f'power: {self.power}')
        print(f'rowingTime: {self.rowingTime}')
        print(f'heartRate: {self.heartRate}')
        print(f'interval: {self.interval}')
        print(f'rec: {self.rec}')
        print(f'isEdge: {self.isEdge}')
        # print(f'total_speed: {self.total_speed}')
        # print(f'total_cadence: {self.total_cadence}')
        # print(f'pedal: {self.pedal}')

        # if self.pedal ==0:
        #     self.avg_speed = self.total_speed / 1
        #     self.avg_cadence = self.total_cadence / 1
        # else:
        #     self.avg_speed = self.total_speed / self.pedal
        #     self.avg_cadence = self.total_cadence / self.pedal
        # if self.workoutTime == 0:
        #     self.avg_cadence = self.strokes/1
        #     self.avg_pace = (1/self.distance)*500
        # else:
        #     self.avg_cadence = self.strokes/self.workoutTime
        #     self.avg_pace = (self.workoutTime/self.distance)*500

        self.woObj = RowerWorkout(
            distance =      self.distance,
            cadence =       self.cadence,
            calories =      self.calories,
            strokes =       self.strokes,
            timestamp =     self.timestamp,        
            workoutTime =   self.workoutTime,
            pace =          self.pace,
            power =         self.power,
            rowingTime =    self.rowingTime,
            heartRate =     self.heartRate,
            interval =      self.interval,
            rec =           self.rec,
            isEdge =        self.isEdge,
        )
        logger.info(f'woObj: {self.woObj}')

        return self.woObj.to_dict()

