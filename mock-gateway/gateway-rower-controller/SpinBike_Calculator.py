from collections import deque
import numpy as np
import pandas as pd
import datetime
import copy

alpha = 0.6             # for ewa filter under Computation, for Power
WHEEL_FACTOR = 5.98     # metre

''' for pedalFlag aka rec in open-api'''
cadenceThres = 0        # to set pedalFlag true
noPedalThres = 10       # n.o. of no pedal count to set pedalflag false

delta_cranktime_thres = 5000

'''for raw data from MQTT without processing'''
class PowerMeterData:

    def __init__(
        self,
        ts,
        power,
        torque,
        crankRevData,
        crankEventTime,
    ):
        self.ts = ts
        self.power = power
        self.torque = torque
        self.crankRevData = crankRevData
        self.crankEventTime = crankEventTime

'''for gateway-processed data'''
class SpinningWorkoutData:

    def __init__(
                 self,
                 crank,
                 delta_cranktime,
                 time_diff,
                 instant_distance,
                 instant_speed,
                 instant_cadence,
                 instant_power,
                 instant_calories,
                 recFlag,
                 ):
        self.crank = crank
        self.delta_cranktime = delta_cranktime
        self.time_diff = time_diff
        self.instant_distance = instant_distance      # distance
        self.instant_speed = instant_speed
        self.instant_cadence = instant_cadence
        self.instant_power = instant_power
        self.instant_calories = instant_calories      # calories
        self.recFlag = recFlag          # pedalFlag

    # creating a dictionary to append data to list during computation
    def to_dict(self):
        return {
                "crank":            self.crank,
                "delta_cranktime":  self.delta_cranktime,
                "time_diff":        self.time_diff,
                "instant_distance": self.instant_distance,
                "instant_speed":    self.instant_speed,
                "instant_cadence":  self.instant_cadence,
                "instant_power":    self.instant_power,
                "instant_calories": self.instant_calories,
                "recFlag":          self.recFlag,  # pedalFlag
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

        if self.prev is not None:

            # check repeated curr from repeated MQTT msg
            self.repeatflag = self.is_currRepeated()
            # self.time_diff = 0
            # self.prevTimeStamp = 0

            if (self.repeatflag == True):
                return None
            else: 
                woDict = self.dataComputation()
                self.throt_queue.append(woDict)
                self.prev = copy.deepcopy(self.curr)
                return woDict

        else:
            self.prev = copy.deepcopy(self.curr)
            self.startTime = self.getCurrentTimestamp()
            return None             # for first row data without prev data

    def is_currRepeated(self):

        delta_ts = self.curr.ts - self.prev.ts

        # check if base module sends repeated mqtt with slight diff in ts
        if (self.curr.crankRevData == self.prev.crankRevData and
            self.curr.power == self.prev.power and
            self.curr.torque == self.prev.torque and 
            self.curr.crankEventTime == self.prev.crankEventTime and
            delta_ts < 200
            ):
            return True
        else:
            return False

    def dataComputation(self):

        #######################################################################
        delta_rev = self.curr.crankRevData - self.prev.crankRevData

        if delta_rev < 0:
            delta_rev = 1
        #######################################################################
        delta_cranktime = (self.curr.crankEventTime - self.prev.crankEventTime)

        if (self.curr.power == 0 and delta_cranktime > delta_cranktime_thres):

            '''
            Case 1: 
            pause workout event with no overflow occurring
            causing exceptionally large delta_cranktime
            resulting in inaccurate metrics derivated from it
            '''

            print('workout continued')
            delta_cranktime = 0

        elif (self.curr.power == 0 and delta_cranktime < 0):

            '''
            Case 2:
            when overflow occurred
            and it's after a pause workout event or start workout event
            start workout event surely cause an overflow 
            due to the time diff from previous workout session
            '''

            print('workout started with crankEventTime overflow!')
            delta_cranktime = 0

        elif (delta_cranktime < 0):

            '''
            Case 3:
            (delta_cranktime < 0) => pre.crankEventTime overflow
            crankEventTime is uint_16 = 65535, => is max
            from '0' to '65535' 
            '''

            print('overflow occurred!')
            val = 65536 - self.prev.crankEventTime
            val = val + self.curr.crankEventTime
            delta_cranktime = val

        # print(f'delta_cranktime: {delta_cranktime}')
        # ps: cases spiltted in this manner for better readability
        #######################################################################
        '''
        Time difference 
        between current and previous MQTT msg, in seconds.
        '''
        self.currTimeStamp = self.getCurrentTimestamp()

        if (self.prevTimeStamp == 0):
            self.time_diff = self.currTimeStamp - self.startTime
        else:
            self.time_diff = self.currTimeStamp - self.prevTimeStamp

        self.prevTimeStamp = self.currTimeStamp

        #######################################################################
        '''
        Distance in km
        5.98 metre travelled per crank event, experiment result.
        '''
        if (delta_cranktime == 0):
            instant_distance = 0.0
        else:
            instant_distance = WHEEL_FACTOR / 1000     # metre to km

        #######################################################################
        '''
        Cadence = RPM, revolution per minute
        1x revolution per delta_cranktime
        1x crankEventTime is 1/1024 seconds
        '''
        if (delta_cranktime == 0):
            instant_cadence = 0.0
        else:
            instant_cadence = (1/delta_cranktime)*(1024*60)
        # print(f'instant_cadence: {instant_cadence} rpm')

        #######################################################################
        '''Speed, m/min to km/h'''
        if (instant_cadence == 0.0):
            instant_speed = 0.0
        else:
            
            instant_speed = (instant_cadence * WHEEL_FACTOR) * (60/1000)
        # print(f'instant_speed: {instant_speed} km/h')

        #######################################################################
        '''
        Power
        applied filter to reduce the spikes from raw power data from sensor
        '''
        ewa_power = alpha*self.curr.power + (1 - alpha)*self.prev.power
        # print(f'ewa_power: {ewa_power}')

        #######################################################################
        '''
        Calories in kcal
        Energy (Joules) = Power (Watts) * Time (seconds) / 1000
        1 Joule = (0.24*1000) Cals
        kcal = Cals (big C)
        '''
        instant_calories = (self.curr.power * self.time_diff) / (1000 * 0.24)
        # print(f'{self.time_diff=}')

        # nullify initial spike in calories due to power spike
        if (instant_calories > 5.0):
            instant_calories = 0.0 
        # print(f'instant_calories {instant_calories} Cals')

        #######################################################################
        '''
        Get Pedal Flag
        '''
        if (instant_cadence > cadenceThres):
            self.pedalFlag = True
            self.noPedalCount = 0
        else:
            self.noPedalCount += 1

            if (self.noPedalCount > noPedalThres):
                self.pedalFlag = False

        #######################################################################
        '''
        dictionary of computed results
        '''
        self.woDataObj = SpinningWorkoutData(
                                    crank=delta_rev,
                                    delta_cranktime=delta_cranktime, 
                                    time_diff=self.time_diff,
                                    instant_distance=instant_distance,
                                    instant_speed=instant_speed,
                                    instant_cadence=instant_cadence,
                                    instant_power=ewa_power,
                                    instant_calories=instant_calories,
                                    recFlag=self.pedalFlag,
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

            sumCals = 0.0
            sumDis = 0.0
            sumSpeed = 0.0
            sumCadence = 0.0
            sumPedal = 0.0
            sum_delta_cranktime = 0
            sum_time_diff = 0.0

            for i in range(self.qLen):

                self.throt_dict        = self.throt_queue.pop()
                print(f'\nthrottled dictionary:\n{self.throt_dict}\n')

                sumPedal            += self.throt_dict["crank"]
                sum_delta_cranktime += self.throt_dict["delta_cranktime"]
                sum_time_diff       += self.throt_dict["time_diff"]

                latest_inst_speed   = self.throt_dict["instant_speed"]

                latest_inst_cadence = self.throt_dict["instant_cadence"]

                latest_inst_power   = self.throt_dict["instant_power"]

                latest_recFlag      = str (self.throt_dict["recFlag"])   #pedalFlag

                sumCals         += self.throt_dict["instant_calories"]
                sumDis          += self.throt_dict["instant_distance"]
                sumSpeed        += self.throt_dict["instant_speed"]
                sumCadence      += self.throt_dict["instant_cadence"]

            '''
            Keys are fixed by endpoint (spinnerUpdateRedis)
            Values are instantaneous and
            fixed as float or str type to fit endpoint
            '''
            toSendD = {
                "speed": latest_inst_speed,
                "cadence": latest_inst_cadence,
                "distance": sumDis,
                "calories": sumCals,
                "power": latest_inst_power,
                "rec": latest_recFlag,
                "workoutTime": sum_time_diff,
                "pedal": sumPedal,
                "total_speed": sumSpeed,
                "total_cadence": sumCadence,
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
