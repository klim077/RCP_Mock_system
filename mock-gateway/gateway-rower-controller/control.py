# import sched

# # import common.config
# import redis
# import sys
# import os
# import importlib
# # from backend.common import config
# import config
# # from random import randintcd
# # import paho.mqtt.client as mqtt
# # from backend.common import mqttwrapper as mqtt
# import mqttwrapper as mqtt
# import time
# import sys
# import redis
# import os
# import pandas as pd
# import pytz
# import json
# import numpy as np
# from collections import deque
# from spinning_bike_parameter import SpinningBikeParameter
# import datetime
# import socketio
# import logging
# import requests
# from threading import Timer

# from collections import deque

# import graypy
# import loggerwrapper

# import orchestratorwrapper as orchestrator

# from smartgymgatewayutils import config as utils_config

# DEBUGMODE = 0  # Fake Data
# CADENCETHRESHOLD = 45

# """Logging Levels
# |Level   |Numeric value|
# |--------|-------------|
# |CRITICAL|50           |
# |ERROR   |40           |
# |WARNING |30           |
# |INFO    |20           |
# |DEBUG   |10           |
# |NOTSET  |0            |
# """

# # Set up logger
# logger = loggerwrapper.LoggerWrapper('treadmill').getLogger()
# logger.info('Static bike logger ready')

# ##############################
# # Modifications for REST API #
# ##############################
# apikey = utils_config.api_key
# protocol = utils_config.protocol
# serverUrl = utils_config.server_url
# logger.info(f'serverUrl = {serverUrl}')

# ##############################
# # Modifications for socketio #
# ##############################
# sio = socketio.Client()
# sio.connect(serverUrl + '/socket.io/')


# @sio.event
# def connect():
#     #print('connected to server ' + str(sio.sid), flush=True)
#     logger.info('Static bike connected to socketio server with id ' + str(sio.sid))

# @sio.event
# def disconnect():
#     #print('disconnected from server', flush=True)
#     logger.info('Static bike ' + str(sio.sid) + ' disconnected from socketio server')


# @sio.event
# def ackmessage(data):
#     #print('Received data: ', data, flush=True)
#     logger.info('Static bike received following data from sockio server: ' + str(data))



# ##########################
# # Availability scheduler #
# ##########################
# # Track last un-availability time
# machineID = None

# available_threshold_seconds = 10
# last_unavailable = datetime.datetime.now()
# thresh_unavailable = datetime.timedelta(seconds=available_threshold_seconds)

# s = sched.scheduler(time.time, time.sleep)

# # Future set availability event object
# futureEvent = None


# def setAvailability(state):
#     logger.info(f'Step into setAvailability({state})')

#     try:

#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/available'
#         headers = {'Content-type': 'application/json',
#                    'Accept': 'application/json', 'X-API-Key': apikey}
#         data = {'value': int(state)}
#         ret = requests.post(
#             url, data=json.dumps(data), headers=headers)
#         print('Set machine availability ' + str(ret))

#     except Exception as e:
#         logger.error(e)

# def setAvailable():
#     logger.info('Step into setAvailable')

#     # Set available on backend server
#     setAvailability(1)


# def setFutureEvent():
#     logger.info('Step into setFutureEvent')
#     global futureEvent
#     futureEvent = s.enter(available_threshold_seconds, 1, setAvailable)


# def setUnavailable():
#     logger.info('Step into setUnavailable')

#     # Set unavailable on backend server
#     setAvailability(0)

#     # # Cancel any previous events first
#     # global futureEvent
#     # try:
#     #     s.cancel(futureEvent)
#     #     logger.info(f'futureEvent canceled')
#     # except Exception as e:
#     #     logger.error(e)

#     # # Schedule availability to be set in the future
#     # setFutureEvent()



# ###########################
# # Modifications for redis #
# ###########################
# # redis_ip = '10.10.3.9'
# # redis_port = 16379
# redis_ip_local = config.local_redis_ip
# redis_port_local = config.local_redis_port
# topic_name = 'bike'
# hostname = os.environ['HOSTNAME']

# ##################################
# # Modifications for orchestrator #
# ##################################


# # Machine ID can be defined because this control runs on only one machine
# # test_machineID = '3d8bcab2966947ff8847449232f886c6'
# machineID = orchestrator.acquireMachineId(
#     ip=redis_ip_local,
#     port=redis_port_local,
#     hostname=hostname,
#     machine_type=topic_name,
# )

# # Name of assigned list
# assigned_key_name = 'assigned'


# WHEEL_FACTOR = 0.78

# def timestamp():
#     return time.time()

# def getCurrentTimestamp():
    
#     now = datetime.datetime.now()
#     timestamp = datetime.datetime.timestamp(now)

#     print(timestamp)

#     return timestamp

# def j(*args):
#     return ':'.join([str(ele) for ele in args])


# class PeriodicTask(object):
#     def __init__(self, interval, callback, daemon=True, **kwargs):
#         self.interval = interval
#         self.callback = callback
#         self.daemon   = daemon
#         self.kwargs   = kwargs

#     def run(self):
#         self.callback(**self.kwargs)
#         t = Timer(self.interval, self.run)
#         t.daemon = self.daemon
#         t.start()


# class SpinningBikeInterface:

#     def __init__(self):

#         # mqtt - subscribing topic
#         self.mqtt_sub_topic = machineID + '/data'
#         # Redis
#         # self.r = self.setUpRedis()
#         # self.r = self.setUpRedisLocal()

#         #availability
#         self.last_unavailable = datetime.datetime.now()
#         self.thresh_unavailable = datetime.timedelta(seconds=10)

#         # Workout Information for bike
#         self.distance = 0  # To simulate the static bike
#         self.calories = 0
#         self.curr_total_distance = 0
#         self.curr_total_distance_2 = 0

#         self.user = ''

#         if DEBUGMODE:
#             self.dummyDf = pd.read_csv('./workout_data2.csv')
#             self.dataLen = self.dummyDf.shape[0]
#             self.dummyIndex = 0

#         else:
#             self.setUpMQTT()
        
    
#         self.curr_cycle_data_dict = None  # PM stands for Power Meter
#         self.prev_cycle_data_dict = None
#         self.currWoDict = None

#         self.workoutTime = 0
#         self.total_cals = 0

#         self._LOG_BOOL = False
#         self.workouts_list = []

#         self.recording_flag = False

#         self.userData = None
#         self.userFileName = ''
#         self.existing_userID = None

#         self.avgCadenceVar = SpinningBikeParameter("avg_cadence", 30)
#         self.avgSpeedVar = SpinningBikeParameter("avg_speed", 30)

#         self.powerVar = SpinningBikeParameter("power", 10)
#         self.cadenceVar = SpinningBikeParameter("cadence", 5)

#         self.workoutDictStack = deque()
#         #print("getMachineName")
#         self.topic_name = 'bike'
#         # topic_name = 'machines'
#         self.hostname = os.environ['HOSTNAME']

#         self.machineID = machineID
#         # try: 
#         #     print("getMachineName")

#         #     # self.machineID = orchestrator.acquireMachineId(self.r, self.topic_name)
#         #     self.machineID = orchestrator.acquireMachineId(
#         #         ip=redis_ip_local,
#         #         port=redis_port_local,
#         #         hostname=self.hostname,
#         #         machine_type=self.topic_name,
#         #     )
#         #     print(f'Processing {self.machineID}', flush=True)

#         # except Exception as e:
#         #     print(e)
#         #     print("get machine didnt work")

        
#         # machineID = self.machineID

#         # print("Machine ID: {}".format(self.machineID))


#     # def getMachineId(self, client, name):
#     #     '''
#     #     Infinite blocking right pop a value from key [name] using [client]

#     #     Returns:
#     #         str: value
#     #     '''
#     #     # Get a machine id from redis list
#     #     # brpop returns a tuple (key, value)
#     #     key, value = client.brpop(name)
#     #     value = value.decode()

#     #     return value


#     # def postMachineId(self, client, machineId, name):
#     #     '''Adds an entry to the assigned list in redis

#     #     Args:
#     #         client: Redis client
#     #         machineId: Machine ID
#     #         name: List name
#     #     Return:
#     #         nil
#     #     '''
#     #     hostname = os.environ['HOSTNAME']
#     #     client.set(j(assigned_key_name, machineId, hostname), name)


#     # def subscribeMachineId(self, client, machineId):
#     #     '''Subscribes to a machineId as channel

#     #     Args:
#     #         client: Redis client
#     #         machineId: Machine ID
#     #     Return:
#     #         nil
#     #     '''
#     #     p = client.pubsub()
#     #     p.subscribe(machineId)


#     # def acquireMachineId(self, client, name):
#     #     '''Acquire a machine ID from redis server

#     #     Args:
#     #         client: Redis client
#     #         name: List name
#     #     Return:
#     #         str: Machine ID
#     #     '''
#     #     machine_id = self.getMachineId(client, name)
#     #     self.postMachineId(client, machine_id, name)
#     #     self.subscribeMachineId(client, machine_id)

#     #     return machine_id


#     def setUpMQTT(self):

#         # Set up MQTT
#         mqtt_uuid_spinner = f'control_spinner_{timestamp()}'
  
#         broker_address = config.broker_address
#         broker_port = config.broker_port
        
#         #mqtt_ip = 'mosquitto'
#         #mqtt_port = 1883

#         print("MQTT Broker: IP: {}, Port: {}".format(
#             broker_address, broker_port))

#         # topic_speed = 'bike/speed'
#         # topic_cadence = 'bike/cadence'
#         self.client = mqtt.MQTTWrapper(mqtt_uuid_spinner)
#         self.client.on_connect = self.cb_on_connect
#         self.client.setup(broker_address, broker_port)
#         self.client.subscribe(self.mqtt_sub_topic)
#         print('subscribed topic: ', self.mqtt_sub_topic)


#         logger.info("setUp MQTT client completed")
#         # self.client.on_message = self.cb_on_message
#         #self.client.connect(broker_address,broker_port)

#     # def setUpRedisLocal(self):
#     #     connected = False

#     #     while(not connected):
#     #         try:
#     #             time.sleep(1)
#     #             r = redis.Redis(redis_ip_local, redis_port_local)
#     #             connected = r.ping()
#     #         except Exception as e:
#     #             print(e)

#     #     print(f'Connected to {redis_ip_local}:{redis_port_local}!', flush=True)

#     #     return r


#     # def setUpRedis(self):

#     #     logger.info("RedisIP {}".format(redis_ip))

#     #     self.r = redis.Redis(redis_ip, redis_port)

#     #     self.r.set('fo o', 4)
#     #     value = self.r.get('fo o')

#     #     if value.decode() == '4':
#     #         print("Redis is Connected")
#     #         return self.r
#     #     else:
#     #         return None

#     def cb_on_connect(self, client, userdata, flags, rc):
#         if rc == 0:
#             print('MQTT Client has been Connected')
#         else:
#             raise Exception('connection refused')

#     def cb_on_message(self, client, userdata, message):
#         msg = message.payload.decode()
#         print('message received:{}'.format(msg))
#         rssi.append(msg)

#     def createDataFrame(self):

#         channel = self.r.get('{mid}:user'.format(mid=self.machineID))
#         self.user = str(channel.decode())

#     def updateWorkoutTime(self):

#         t_diff = self.curr_cycle_data_dict["timestamp"] - self.prev_cycle_data_dict["timestamp"]
#         self.workoutTime = self.workoutTime + t_diff
#         print("Updated Workout Time: {}:".format(self.workoutTime))

#     def trapz_area(self, x0, x1, y0, y1):

#         A = 0.5*((x1 - x0)/1000) * (y1 + y0)  # MilliSeconds to Seconds
#         return A

#     def updateWorkoutData(self):

#         if self.prev_cycle_data_dict != None:

#             if(self.prev_cycle_data_dict["rec"] is True and 
#                 self.curr_cycle_data_dict["rec"] is True):

#                 print("WORKINGOUT")

#                 self.updateWorkoutTime()

#                 x0 = self.prev_cycle_data_dict["ts"]
#                 y0 = self.prev_cycle_data_dict["speed"]
#                 x1 = self.curr_cycle_data_dict["ts"]
#                 y1 = self.curr_cycle_data_dict["speed"]

#                 dis = self.trapz_area(x0, x1, y0, y1)
#                 self.distance = dis
#                 distance_km = self.distance/1000
#                 self.curr_total_distance = self.curr_total_distance + distance_km

#                 #Distance Calc #2
#                 x0 = self.prev_cycle_data_dict["timestamp"]
#                 y0 = self.prev_cycle_data_dict["speed"]
#                 x1 = self.curr_cycle_data_dict["timestamp"]
#                 y1 = self.curr_cycle_data_dict["speed"]

#                 dis = self.trapz_area(x0*1000, x1*1000, y0, y1)
#                 distance2_km = dis/1000

#                 #self.curr_total_distance_2 = self.curr_total_distance_2 + distance2_km

#                 #print("dis: {}, dis2: {}".format(distance_km, distance2_km))
#                 #print("TDis: {} TDis2: {}".format(self.curr_total_distance,self.curr_total_distance_2))


#                 avgPower = self.powerVar.getMovingAverage()
#                 # avgPower = 0 if a is Nan else y
#                 self.updateAverages()
#                 avgCadence = self.avgCadenceVar.getMovingAverage()
#                 avgSpeed = self.avgSpeedVar.getMovingAverage()

#                 cals = self.curr_cycle_data_dict["cals"]/1000
#                 #self.total_cals += cals
#                 woTime = self.curr_cycle_data_dict["timestamp"] - self.prev_cycle_data_dict["timestamp"]
        
#                 workoutDict = {"ts": self.curr_cycle_data_dict["ts"],
#                                "power": self.curr_cycle_data_dict["power"],
#                                "ma_power": avgPower,
#                                "cadence": self.curr_cycle_data_dict["cadence"],
#                                "speed": self.curr_cycle_data_dict["speed"],
#                                "distance": self.curr_cycle_data_dict["dis"]/1000,#distance2_km,
#                                "calories": cals,
#                                "avg_cadence": avgCadence,
#                                "avg_speed": avgSpeed,
#                                "workoutTime": woTime}

#                 #logger.debug(workoutDict)
            
#                 return workoutDict
#             else:
#                 if self.curr_cycle_data_dict["rec"] is False:
#                     print("WORKOUT IS PAUSED")
#                 return None


# #    def getRecFlag(self):

#         #DEPRECATED

#         # self.recording_flag = str(self.r.get(
#         #     '{mid}:rec'.format(mid=machineID)).decode())

#         # if (self.recording_flag == "True"):
#         #     return True
#         # else:
#         #     return False



#     def checkUserPedalling(self):

#         #Check that the user is pedalling and updates redis if the flag has changed
#         logger.debug("checkPedalling, current CADENCE: {}".format(self.curr_cycle_data_dict["cadence"]))
#         self.curr_cycle_data_dict["rec"] = True if self.curr_cycle_data_dict["cadence"] > CADENCETHRESHOLD else False

#         if self.recording_flag != self.curr_cycle_data_dict["rec"]:
#             self.updateRec(self.curr_cycle_data_dict["rec"])
#             self.recording_flag = self.curr_cycle_data_dict["rec"]

#             if self.recording_flag:
#                 setUnavailable()
#             else:
#                 setAvailable()

#     def updateAverages(self):

#         self.powerVar.updateCurrentVal(self.curr_cycle_data_dict["power"])
#         self.cadenceVar.updateCurrentVal(self.curr_cycle_data_dict["cadence"])
#         self.avgCadenceVar.updateCurrentVal(
#             self.curr_cycle_data_dict["cadence"])
#         self.avgSpeedVar.updateCurrentVal(self.curr_cycle_data_dict["speed"])
    
#     def run_mqtt_client_2(self):

#         # received_df = pd.DataFrame(columns = ["ts", "power,", "cadence", "speed"])
#         # Run Publisher of Exercise data:
#         #print("Running")

#         power_data_str, _ = self.client.next(1/10)

#         # print("client, received data {}", power_data_str)
#         self.curr_cycle_data_dict = json.loads(power_data_str)
#         #Add timeStamp

#         if isinstance(self.curr_cycle_data_dict, dict):

#             self.curr_cycle_data_dict["timestamp"] = getCurrentTimestamp()
#             #self.curr_cycle_data_dict["rec"] = True if self.curr_cycle_data_dict["cadence"] > CADENCETHRESHOLD else False
#             self.checkUserPedalling()

#             # Process data to calculate Distance
#             self.currWoDict = self.updateWorkoutData()
            

#             self.prev_cycle_data_dict = self.curr_cycle_data_dict.copy()

#             if self.currWoDict is not None:
#                 print("WoDict is not None, not Paused")
#                 return self.currWoDict
        
#         else: 
#             return None 

            

#     def run_mqtt_client(self):

#         # received_df = pd.DataFrame(columns = ["ts", "power,", "cadence", "speed"])
#         # Run Publisher of Exercise data:
#         print("Running")

#         test_counter = 1

#         while True:
#             try:
#                 power_data_str, _ = self.client.next(1/10)

#                 # print("client, received data {}", power_data_str)
#                 self.curr_cycle_data_dict = json.loads(power_data_str)

#                 if isinstance(self.curr_cycle_data_dict, dict):
#                     # Process data to calculate Distance
#                     wodict = self.updateWorkoutData()

#                     # print(self.curr_cycle_data_dict)
#                     self.prev_cycle_data_dict = self.curr_cycle_data_dict.copy()

#             except KeyboardInterrupt:
#                 print('Interrupted')
#                 df = pd.DataFrame(self.workouts_list, columns=[
#                                   "ts", "power", "cadence", "speed", "distance", "calories"])
#                 df.to_pickle("workoutdata")
#                 print("Saved Data")
#                 sys.exit(0)

#     def publish_dummy_df_2(self):

#         # Run Publisher of Exercise data:
#         print("Dummy data Running")

#         self.curr_cycle_data_dict = self.dummyDf.iloc[self.dummyIndex, :].to_dict()
#         print(self.curr_cycle_data_dict)


#         woData = self.updateWorkoutData()
#         # if woData != None:
#         #     self.update_redis(woData)

#         self.prev_cycle_data_dict = self.curr_cycle_data_dict.copy()
#         time.sleep(0.5)
#         self.dummyIndex = self.dummyIndex + 1

#         if self.dummyIndex == self.dataLen - 1:
#             self.dummyIndex = 0
#             print("StartAgain")

#         return woData

#     def publish_dummy_df(self):

#         # Run Publisher of Exercise data:
#         print("Dummy data Running")

#         df = pd.read_csv('./workout_data2.csv')
#         # print(df.columns)

#         endOfFile = False
#         while not endOfFile:
#             try:
#                 woDicList = []
#                 for inx, range in df.iterrows():

#                     self.curr_cycle_data_dict = range.to_dict()
#                     # print(self.curr_cycle_data_dict)

#                     woData = self.updateWorkoutData()

#                     # print("PowerVar {}".format(self.powerVar.getMovingAverage()))
#                     # print("AvgCadenceVar: {}".format(self.avgCadenceVar.getMovingAverage()))

#                     if woData != None:

#                         woDicList.append(woData)

#                     self.prev_cycle_data_dict = self.curr_cycle_data_dict.copy()

#                     time.sleep(1)

#                 enOfFile = True

#                 dataFrame = pd.DataFrame(woDicList)
#                 file_name = str(datetime.datetime.now()).split(".")[0] + ".csv"
#                 dataFrame.to_csv(file_name)
#                 # Reset All Fiels on Redis
#                 print("Resetting WorkOut Vars")
#                 #self.distance = 0
#                 #self.calories = 0

#             except KeyboardInterrupt:
#                 sys.exit(0)

#     def update_redis(self, woData):

#         machineID = self.machineID

#         channel = self.r.get('{mid}:user'.format(mid=machineID))

#         self.user = str(channel.decode())

#         # print("Self User: {}".format(self.user))

#         self.recording_flag = str(self.r.get(
#             '{mid}:rec'.format(mid=machineID)).decode())

#         # print("recording_flag: {}".format(self.recording_flag))

#         # if (self.recording_flag == "False"):
#             # self.last_wo_distance = distance
#             # print("Flag is False")
#             # self.distance = 0
#             # self.calories = 0
#         # else:
#         # print("woData", woData)

#         # self.r.set('{mid}:power'.format(mid=machineID),woData["power"])
#         self.r.set('{mid}:power'.format(mid=machineID), woData["ma_power"])
#         self.r.set('{mid}:speed'.format(mid=machineID), woData["speed"])
#         self.r.set('{mid}:cadence'.format(mid=machineID), woData["cadence"])
#         # self.r.set('{mid}:distance'.format(mid=machineID),woData["distance"])
#         self.r.incrbyfloat('{mid}:distance'.format(
#             mid=machineID), woData["distance"])
#         # self.r.set('{mid}:calories'.format(mid=machineID),woData["calories"])
#         self.r.incrbyfloat('{mid}:calories'.format(
#             mid=machineID), woData["calories"])
#         self.r.set('{mid}:avgSpeed'.format(mid=machineID), woData["avg_speed"])
#         self.r.set('{mid}:avgCadence'.format(
#             mid=machineID), woData["avg_cadence"])

#         # print(j(machineID,'data_stream'))
#         self.r.xadd(j(machineID, 'data_stream'), fields=woData)

#         # print(j(machineID,'speed'))
#         self.r.publish(channel, '{mid}:speed'.format(
#             mid=machineID))  # Notify app

#     def updateRec(self, isRec):

#         machineID = self.machineID
#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/rec'
#         logger.debug("update redis post: " + url) 
#         headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         data = {'value': str(isRec)}
#         ret = requests.post(url, data=json.dumps(data), headers=headers)
#         logger.info('Set REC ' + str(ret) + ' ' + str(isRec))


#     def update_redis_callback(self):

#         #logger.debug("periodic callback, size of Stack: {}".format(len(self.workoutDictStack)))

#         if self.recording_flag == True and len(self.workoutDictStack) > 0:
            
#             #get current queue Length
#             qLen = len(self.workoutDictStack)
#             logger.debug("#items in queue: {}".format(qLen))

#             sumCals = 0
#             sumWoTime = 0
#             sumDis = 0
#             for i in range(qLen):
#                 wDict = self.workoutDictStack.popleft()
#                 sumCals += wDict["calories"] 
#                 sumDis += wDict["distance"]
#                 sumWoTime += wDict["workoutTime"]

#             toSendDict = {#"ts": wDict["ts"],
#                                #"power": wDict["power"],
#                                "power": wDict["ma_power"],
#                                "cadence": wDict["cadence"],
#                                "speed": wDict["speed"],
#                                "distance": sumDis,
#                                "calories": sumCals,
#                                "avgCadence": wDict["avg_cadence"],
#                                "avgSpeed": wDict["avg_speed"],
#                                "workoutTime": sumWoTime}

#             logger.debug("Updating Redis with:{}".format(toSendDict))

#             #self.update_redis_2(toSendDict)
#             self.update_redis_3(toSendDict)
#             #Reset currWoDict
#             self.currWoDict = None
#         else:
#             logger.debug("")


#     def update_redis_2(self, woData):
        
#         machineID = self.machineID

#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues'   
#         #logger.debug("update redis post: " + url) 
#         headers = {'Accept': 'application/json', 'X-API-Key': apikey}
#         ret = requests.get(url, headers=headers)
#         data = ret.json()
#         #prev_wt = data['weight']
#         channel = data['user']
#         print('Get the channel name ' + str(ret) + ' ' + str(channel))

#         # Increment distance
#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/distance/increment'
#         headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         data = {'value': woData['distance']}
#         ret = requests.post(url, data=json.dumps(data), headers=headers)
#         print('distance ' + str(ret) + ' ' + str(woData['distance']))

#         # # Increment calories
#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/calories/increment'
#         headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         data = {'value': woData['calories']}
#         ret = requests.post(url, data=json.dumps(data), headers=headers)
#         print('Calories ' + str(ret) + ' ' + str(woData['calories']))

#         # Increment WorkOut Time
#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/workoutTime/increment'
#         headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         data = {'value': woData['workoutTime']}
#         ret = requests.post(url, data=json.dumps(data), headers=headers)
#         print('workoutTime ' + str(ret) + ' ' + str(woData['workoutTime']))

#         # url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/distance'
#         # logger.debug("update redis post: " + url) 
#         # headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         # data = {'value': woData["distance"]}
#         # ret = requests.post(url, data=json.dumps(data), headers=headers)
#         # print('Set distance ' + str(ret) + ' ' + str(woData["distance"]))

#         # url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/calories'
#         # logger.debug("update redis post: " + url) 
#         # headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         # data = {'value': woData["calories"]}
#         # ret = requests.post(url, data=json.dumps(data), headers=headers)
#         # print('Set calories ' + str(ret) + ' ' + str(woData["calories"]))


#         # url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/workoutTime'
#         # logger.debug("update redis post: " + url) 
#         # headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         # data = {'value': woData["workoutTime"]}
#         # ret = requests.post(url, data=json.dumps(data), headers=headers)
#         # print('Set workoutTime ' + str(ret) + ' ' + str(woData["workoutTime"]))


#         # # Set Power
#         # r.set(j(machineID, 'weight'), wt_kg)
#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/power'
#         logger.debug("update redis post: " + url) 
#         headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         data = {'value': woData["ma_power"]}
#         ret = requests.post(url, data=json.dumps(data), headers=headers)
#         print('Set Bike Power ' + str(ret) + ' ' + str(woData["ma_power"]))

#         # # Set Speed
#         # r.set(j(machineID, 'weight'), wt_kg)
#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/speed'
#         headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         data = {'value': woData["speed"]}
#         ret = requests.post(url, data=json.dumps(data), headers=headers)
#         print('Set Bike Speed ' + str(ret) + ' ' + str(woData["speed"]))

#         # # Set Cadence
#         # r.set(j(machineID, 'cadence'), cadence)
#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/cadence'
#         headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         data = {'value': woData["cadence"]}
#         ret = requests.post(url, data=json.dumps(data), headers=headers)
#         print('Set Bike Cadence ' + str(ret) + ' ' + str(woData["cadence"]))

#         # # avgSpeed
#         # r.set(j(machineID, 'avgSpeed'), avgSpeed)
#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/avgSpeed'
#         headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         data = {'value': woData["avg_speed"]}
#         ret = requests.post(url, data=json.dumps(data), headers=headers)
#         print('Set Bike AvgSpeed ' + str(ret) + ' ' + str(woData["avg_speed"]))

#         # # avgCadence
#         # r.set(j(machineID, 'avgCadence'), avgCadence)
#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/avgCadence'
#         headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         data = {'value': woData["avg_cadence"]}
#         ret = requests.post(url, data=json.dumps(data), headers=headers)
#         print('Set Bike AvgCadence ' + str(ret) + ' ' + str(woData["avg_cadence"]))

#         # print(j(machineID,'speed'))
#         #self.r.publish(channel, '{mid}:speed'.format(
#         #    mid=machineID))  # Notify app

#         # r.xadd(j(machineID, 'data_stream'), fields=data)
#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/data_stream/xadd'
#         headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}
#         ret = requests.post(url, data=json.dumps(woData), headers=headers)
#         print('Set stream with data ' + str(ret))

#         # # Set machine availability
#         # r.set(j(machineID, 'available'), 0)
#         url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues/available'
#         headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         data = {'value': 0}
#         ret = requests.post(url, data=json.dumps(data), headers=headers)
#         print('Set machine availability ' + str(ret))


#         self.last_unavailable = datetime.datetime.now()

#         # Let the client know an update is available    
#         if channel:
#             print('Let the client know an update is available')
#             message = {
#                 'channel': channel,
#                 'machineIDreps': j(machineID, 'speed')
#             }        
#             y = json.dumps(message)
#             sio.emit('message', y)

#     def update_redis_3(self, woData):

#         try: 

#             machineID = self.machineID

#             url = serverUrl + '/v0.1/machines/' + machineID + '/keyvalues'   
#             #logger.debug("update redis post: " + url) 
#             headers = {'Accept': 'application/json', 'X-API-Key': apikey}
#             ret = requests.get(url, headers=headers)
#             data = ret.json()

#             logger.debug(apikey)
#             logger.debug(data)
#             #prev_wt = data['weight']
#             channel = data['user']
#             print('Get the channel name ' + str(ret) + ' ' + str(channel))


#             url = serverUrl + '/v0.1/machines/' + self.machineID + '/spinnerUpdateRedis'
#             headers = {'Content-type': 'application/json',
#             'Accept': 'application/json', 'X-API-Key': apikey}
#             data = woData
#             ret = requests.post(url, data=json.dumps(data), headers=headers)
#             logger.debug('Calling spinnerUpdateRedis ' + str(ret))

#             if channel:
#                 print('Let the client know an update is available')
#                 message = {
#                     'channel': channel,
#                     'machineIDreps': j(machineID, 'speed')
#                 }        
#                 y = json.dumps(message)
#                 sio.emit('message', y)

#         except Exception as e:
#             logger.error(e)



# def main():

#     sens_publisher = SpinningBikeInterface()
#     logger.info("created SB Sensor Interface Object")

#     if  DEBUGMODE:
#         logger.info("Starting Sensor Publisher in DEBUGMODE")

#         data_acq_func = sens_publisher.publish_dummy_df_2
#         #sens_publisher.publish_dummy_df()
#         print("DEBUGMODE FUNCTION CHOSEN")

#     else:
#         logger.info("Starting sensor publisher in LIVE mode")
#         data_acq_func = sens_publisher.run_mqtt_client_2

#     periodicTasks = PeriodicTask(interval = 1, callback = sens_publisher.update_redis_callback)
#     periodicTasks.run()

#     logger.info("Starting Loop")
#     while True:
#         # Run availability scheduler
#         s.run(blocking=False)
#         # try:
#         #     url = serverUrl + '/v0.1/machines/' + sens_publisher.machineID + '/keyvalues'
#         #     headers = {'Accept': 'application/json', 'X-API-Key': apikey}
#         #     ret = requests.get(url, headers=headers)
#         #     print()
#         #     data = ret.json()
#         #     available = data['available']
#         #     print('Check available time threshold ' +
#         #         str(ret) + ' ' + str(available))
            
#         #     if available == False:
#         #         diff_available = datetime.datetime.now() - sens_publisher.last_unavailable
#         #         if diff_available > sens_publisher.thresh_unavailable:
#         #             # r.set(j(machineID, 'available'), 1)
#         #             url = serverUrl + '/v0.1/machines/' + sens_publisher.machineID + '/keyvalues/available'
#         #             headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-API-Key': apikey}    
#         #             data = {'value': 1}
#         #             ret = requests.post(url, data=json.dumps(data), headers=headers)
#         #             print('Set machine availability ' + str(ret))
    
#         # except Exception as e:
#         #     logger.error(e)
        
#         currWoDict = data_acq_func()
#         if currWoDict != None:
#             logger.debug("received data and appending to stack")
#             sens_publisher.workoutDictStack.append(currWoDict)


#         #if ret != None:
#             #logger.info("received data via MQTT")
#             #sens_publisher.update_redis(ret)
#             #logger.info('calling updateRedis_2')
#             #sens_publisher.update_redis_2(ret)




# if __name__ == "__main__":
#     main()
