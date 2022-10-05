import os
import time
import pandas as pd
import numpy as np

import Rower_Calculator as calculator

import smartgymgatewayutils.abstractworkout as abstractworkout
# import smartgymgatewayutils.gwLogger
# loggerWrapper 
# logger
from smartgymgatewayutils.gwLogger import logger, loggerWrapper
from common.utils import PeriodicTask
from collections import deque

# Get hostname
# hostname = os.environ['HOSTNAME']
hostname = 'SmartGymInABox'
class RowerController(abstractworkout.AbsWorkout):

    def __init__(self, machineType):

        self.workoutData = None
        self.endpoint = 'rowerUpdateRedis'
        super().__init__(machineType)

        #setup logger
        self.loggerName = '{}_{}'.format(machineType, hostname)
        loggerWrapper.start(self.loggerName)
        # loggerWrapper.start(name='rower_SmartGymInABox')

        self.workoutProcessor = calculator.WorkoutProcessor()

        # handles polling
        self.pTask = PeriodicTask(
                interval=1,
                callback=self.sendRedis,
        )

        self.pTask.run()

    def start(self):

        super().startController()

    def sendRedis(self):

        ret = self.workoutProcessor.checkQueue()

        if ret is not None:
            print('\nSend Workout to Redis\n')
            loggerWrapper.info(ret)
            self.addWorkoutDataToQueue(ret, self.endpoint)
        else:
            print('\nNothing in throttling queue\n')

    def processWorkout(self, msg_dict):    #from abstractworkout class

        try:
            if isinstance(msg_dict, dict):

                self.workoutStarted = True
                print(f'\n\nWorkout started {self.workoutStarted}')

                curr_raw = calculator.JetsonData(
                                    timestamp = msg_dict["timestamp"],
                                    distance=msg_dict["distance"],
                                    cadence = msg_dict["cadence"],
                                    calories = msg_dict["calories"],
                                    strokes = msg_dict["strokes"],
                                    workoutTime = msg_dict["workoutTime"],
                                    pace = msg_dict["pace"],
                                    power = msg_dict["power"],
                )

                loggerWrapper.info(
                    '\nRaw Data: ' 
                    f'timestamp:  {curr_raw.timestamp}, '
                    f'distance:  {curr_raw.distance}, '
                    f'cadence:  {curr_raw.cadence}, '
                    f'calories:  {curr_raw.calories}, '
                    f'strokes:  {curr_raw.strokes}, '
                    f'workoutTime:  {curr_raw.workoutTime}, '
                    f'pace:  {curr_raw.pace}, '
                    f'Power: {curr_raw.power}, '
                )

                self.workoutProcessor.updateCurrentValue(curr_raw)
                workoutJsonData = self.workoutProcessor.processCurrentWoData()
                # print(workoutJsonData)

        except Exception as e:

                print('No MQTT Data')
                print(e)


if __name__ == "__main__":

    sbc = RowerController("rower")
    sbc.start()
