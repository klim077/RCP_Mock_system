from collections import deque
import numpy as np
import pandas as pd
import datetime
import copy

        #    distance =      self.distance,
        #     cadence =       self.cadence,
        #     calories =      self.calories,
        #     strokes =       self.strokes,
        #     timestamp =     self.timestamp,        
        #     workoutTime =   self.workoutTime,
        #     pace =          self.pace,
        #     power =         self.power,
        #     rec =           self.rec,

''' for pedalFlag aka rec in open-api'''
cadenceThres = 0        # to set pedalFlag true
noPedalThres = 10       # n.o. of no pedal count to set pedalflag false

delta_cranktime_thres = 5000

''' for filtering to ensure data spikes are not recorded'''
distanceFilterThres = 10.0
caloriesFilterThres = 10.0
strokesFilterThres = 10.0
rowingTimeFilterThres = 1000.0

'''for raw data from MQTT without processing'''
class JetsonData:

    def __init__(
        self,
        timestamp,
        distance,
        cadence,
        calories,
        strokes,
        workoutTime,
        pace,
        power,
        rowingTime,
        interval,
        heartRate
    ):
        self.timestamp = timestamp
        self.distance = distance
        self.cadence = cadence
        self.calories = calories
        self.strokes = strokes
        self.workoutTime = workoutTime
        self.pace = pace
        self.power = power
        self.rowingTime = rowingTime
        self.interval = interval
        self.heartRate = heartRate


'''for gateway-processed data'''
class RowerWorkoutData:

    def __init__(
                 self,
                 distance,
                 cadence,
                 calories,
                 strokes,
                 workoutTime,
                 timestamp,
                 pace,
                 power,
                 rowingTime,
                 interval,
                 heartRate,
                 rec,
                 ):
        self.distance = distance
        self.cadence = cadence
        self.calories = calories
        self.strokes = strokes
        self.workoutTime = workoutTime
        self.timestamp = timestamp
        self.pace = pace
        self.power = power
        self.rowingTime = rowingTime
        self.heartRate =heartRate
        self.interval = interval
        self.rec = rec          # pedalFlag

    # creating a dictionary to append data to list during computation
    def to_dict(self):
        return {
                "distance":         self.distance,
                "cadence":  self.cadence,
                "calories":        self.calories,
                "strokes": self.strokes,
                "workoutTime":    self.workoutTime,
                "timestamp": self.timestamp,
                "pace":  self.pace,
                "power":    self.power,
                "rowingTime": self.rowingTime,
                "heartRate": self.heartRate,
                "interval": self.interval,
                "rec":          self.rec,  # pedalFlag
                }

''' Actual processor (running and computing)'''
class WorkoutProcessor:

    def __init__(
                 self,
                 raw_data = None,
                 ):

        self.raw_data = raw_data    # incoming JSON MQTT data
        self.prev = None            # previous data
        self.curr = None            # current data
        self.wo_data_curr = None
        self.wo_data_prev = None
        self.woDataObj ={}
        self.time_diff = 0
        self.prevTimeStamp = 0
        self.pedalFlag = False

        self.throt_queue = deque()

        print("Created WorkoutProcessor")

    # used in control2 to update curr for processCurrentWoData()
    def updateCurrentValue(self, curr):

        self.curr = copy.deepcopy(curr)

    # the main method for workout processing
    def processCurrentWoData(self):

        self.prev_ewa_cadence = 0
        self.noPedalCount = 0
        
        # Clean self.curr to ensure no None values
        self.handleNoneValues()

        self.checkIfRestarted()

        if self.prev is not None:

            # check repeated curr from repeated MQTT msg
            self.repeatflag = self.is_currRepeated()
            # self.time_diff = 0
            # self.prevTimeStamp = 0

            if (self.repeatflag == True):
                return None
            # else: 
            #     woDict = self.dataComputation()
            #     self.throt_queue.append(woDict)
            #     self.prev = copy.deepcopy(self.curr)
            #     return woDict
            else:
                self.sensibleCheck = self.isCurrSensible()
                if (self.sensibleCheck == False):
                    return None
                else:
                    self.filterSpikes()
                    woDict = self.dataComputation()
                    self.throt_queue.append(woDict)
                    self.prev = copy.deepcopy(self.curr)
                    return woDict

        else:
            self.prev = copy.deepcopy(self.curr)
            self.startTime = self.getCurrentTimestamp()
            return None             # for first row data without prev data

    def is_currRepeated(self):

        delta_ts = self.curr.timestamp - self.prev.timestamp

        # check if base module sends repeated mqtt with slight diff in ts
        if (self.curr.distance == self.prev.distance and
            self.curr.cadence == self.prev.cadence and
            self.curr.calories == self.prev.calories and 
            self.curr.strokes == self.prev.strokes and
            self.curr.workoutTime == self.prev.workoutTime and
            self.curr.pace == self.prev.pace and
            self.curr.power == self.prev.power and
            delta_ts < 200
            ):
            return True
        else:
            return False

    def dataComputation(self):

        #######################################################################
        '''
        Get Pedal Flag
        '''
        if (self.curr.power > cadenceThres):
            self.pedalFlag = True
            self.noPedalCount = 0
        # if (self.curr.rowingTime > self.prev.rowingTime):
        #     self.pedalFlag = True
        #     self.noPedalCount = 0
        else:
            self.noPedalCount += 1

            if (self.noPedalCount > noPedalThres):
                self.pedalFlag = False

        #######################################################################
        '''
        dictionary of computed results
        '''
        self.woDataObj = RowerWorkoutData(
                                    distance=self.curr.distance,
                                    cadence=self.curr.cadence, 
                                    calories=self.curr.calories,
                                    strokes=self.curr.strokes,
                                    workoutTime=self.curr.workoutTime,
                                    pace=self.curr.pace,
                                    power=self.curr.power,
                                    rowingTime=self.curr.rowingTime,
                                    heartRate=self.curr.heartRate,
                                    interval= self.curr.interval,
                                    rec=self.pedalFlag,
                                    timestamp=self.curr.timestamp,
                                    )

        return self.woDataObj.to_dict()
    ###########################################################################

    def checkQueue(self):
        '''
        Method to be called to check amount of MQTT msg accumulated.
        This is used by the throttler, a periodic task
        Collect MQTT msg are appended to self.throt_queue
        and only send to backend in a fixed frequency
        so the backend will not be overwhelmed 
        '''

        self.qLen = len(self.throt_queue)
        # print(f'length of throt_queue: {self.qLen}\n')

        if (self.qLen > 0):

            ret = self.throt_callback(self.throt_queue)
            # print(f'\nret: {ret}')
            print('\nclearing throt_queue')
            self.throt_queue.clear()
            self.qLen = len(self.throt_queue)       # should get a "0"
            print(f'length of throt_queue: {self.qLen}\n')

            return ret


    def throt_callback(self, throt_queue):
        '''
        Throttler
        base on collected MQTT msg over a fixed period:
        - only sending the latest instantaneous metrics to backend
        - summing metrics that requires accumulation in backend
        - packaging these data into 1x packet as instaneouse value
        for backend processing 
        '''

        self.throt_queue = throt_queue

        # get current queue length
        self.qLen = len(self.throt_queue)
        
        print(f'periodic callback, size of throt_queue: {self.qLen}')

        if (self.qLen > 0):

            for i in range(self.qLen):

                self.throt_dict        = self.throt_queue.pop()
                print(f'\nthrottled dictionary:\n{self.throt_dict}\n')

                latest_distance   = self.throt_dict["distance"]

                latest_cadence = self.throt_dict["cadence"]

                latest_calories   = self.throt_dict["calories"]

                latest_strokes   = self.throt_dict["strokes"]

                latest_workoutTime   = self.throt_dict["workoutTime"]

                latest_timestamp = self.throt_dict["timestamp"]

                latest_pace   = self.throt_dict["pace"]

                latest_power   = self.throt_dict["power"]

                latest_rowingTime   = self.throt_dict["rowingTime"]

                latest_heartRate    = self.throt_dict["heartRate"]

                latest_interval = self.throt_dict["interval"]

                latest_rec      = str (self.throt_dict["rec"])   #pedalFlag

            '''
            Keys are fixed by endpoint (spinnerUpdateRedis)
            Values are instantaneous and
            fixed as float or str type to fit endpoint
            '''
            toSendD = {
                "distance": latest_distance,
                "cadence": latest_cadence,
                "calories": latest_calories,
                "strokes": latest_strokes,
                "workoutTime": latest_workoutTime,
                "timestamp": latest_timestamp,
                "pace": latest_pace,
                "power": latest_power,
                "rowingTime": latest_rowingTime,
                "heartRate": latest_heartRate,
                "interval": latest_interval,
                "rec": latest_rec,
            }
            print(f'toSendD:\n{toSendD}')

            return toSendD
        else:
            return None

        '''ps note:'''
        # workoutTime is not used for computation in backend & frontend
        # it is prone to network packet lost in transmission
        # instead the difference between start workout and 
        # end workout timestamp is used. Set in exercise-postman-worker
        # workoutTime is kept for cross checking in future

    def getCurrentTimestamp(self):

        now = datetime.datetime.now()
        timestamp = datetime.datetime.timestamp(now)
        # print(f'timestamp: {timestamp}')

        return timestamp

    def handleNoneValues(self):
        attributes = [a for a in dir(self.curr) if not a.startswith('__') and not callable(getattr(self.curr, a))]
        for i in attributes:
            name = i
            if (getattr(self.curr, name) == None and self.prev == None):
                setattr(self.curr, name, 0.00)
            elif(getattr(self.curr, name) == None and self.prev != None):
                prevvalue = getattr(self.prev, name)
                setattr(self.curr, name, prevvalue)

    def isCurrSensible(self):
        if (self.curr.distance >= self.prev.distance and
            self.curr.calories >= self.prev.calories and 
            self.curr.strokes >= self.prev.strokes
            ):
            return True
        else:
            return False
        
    def filterSpikes(self):
        if ((self.curr.distance - self.prev.distance) >= distanceFilterThres):
            self.curr.distance = self.prev.distance
        if ((self.curr.calories - self.prev.calories) >= caloriesFilterThres):
            self.curr.calories = self.prev.calories
        if ((self.curr.strokes - self.prev.strokes) >= strokesFilterThres):
            self.curr.strokes = self.prev.strokes

    def checkIfRestarted(self):
        if ((self.prev !=None) and (self.curr.rowingTime < self.prev.rowingTime)):
            self.prev = None
        
