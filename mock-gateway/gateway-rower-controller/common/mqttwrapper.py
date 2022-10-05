import paho.mqtt.client as mqtt
import time


class MQTTWrapper(mqtt.Client):
    # Connection Return Codes
    # 0: Connection successful
    # 1: Connection refused – incorrect protocol version
    # 2: Connection refused – invalid client identifier
    # 3: Connection refused – server unavailable
    # 4: Connection refused – bad username or password
    # 5: Connection refused – not authorised
    # 6-255: Currently unused.
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f'Connected to mosquitto', flush=True)
        else:
            raise Exception('connection refused')

    def on_message(self, client, userdata, message):
        self.msg = message.payload.decode()
        # print('message received:{}'.format(msg))

    # def sub(self,topic,qos=0):
    #   self.topic = topic
    #   self.qos = qos
    #   self.subscribe(self.topic,self.qos)

    def setup(self, ip, port):
        self.ip = ip
        self.port = port
        mqtt_connect = False
        while not mqtt_connect:
            try:
                # keepalive for 8.5 hrs
                self.connect(self.ip, self.port, 30600)
                mqtt_connect = True
            except ConnectionRefusedError as e:
                print(e)
                time.sleep(1)
        self.msg = 0.0

    def next(self, blocking_time=1/2000):
        self.msg = '-1'
        self.blocking_time = blocking_time
        self.loop(self.blocking_time)
        # print(self.msg)
        return self.msg, self.msg != '-1'

    # def join(self,ip,port):
    #   self.ip = ip
    #   self.port = port
    #   self.connect(self.ip,self.port)

    # def pub(self,topic,payload,qos=0):
    #   self.topic = topic
    #   self.payload = payload
    #   self.qos = qos
    #   self.publish(self.topic,self.payload,self.qos)
