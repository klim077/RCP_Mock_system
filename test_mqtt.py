# from treadmill.src.shared.config import mqtt_port, root_ca

from code import InteractiveConsole
import paho.mqtt.client as paho
import ssl
import time
import json

# mqtt_ip = '192.168.1.119'
mqtt_ip = 'localhost'
mqtt_port = 31883
# root_ca = './treadmill/src/certs/root_ca.crt'
root_ca = 'mock-gateway/work/mosquitto/certs/root_ca.crt'

class MQTT():
    def __init__(self, mqtt_ip):
        self.conn_flag = False
        
        self.mqtt_ip = mqtt_ip

        # Generate timestamp to use as uuid
        self.uuid = str(int(time.time()))

        # Set up MQTT client
        self.client = paho.Client(self.uuid)
        self.client.on_log = self.on_log
        self.client.tls_set(
            ca_certs=root_ca,
        )

        # Do insecure connection as a workaround
        self.client.tls_insecure_set(True)

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

    def connect(self):
        # Connect to MQTT broker
        print("connect function")
        ret = self.client.connect(self.mqtt_ip, mqtt_port)
        print("connect ret: {}".format(ret))
        
        while not self.conn_flag:
            time.sleep(1)
            print('Connection status', self.conn_flag)
            self.client.loop()

        return self

    def start(self):
        self.client.loop_start()

        return self

    def stop(self):
        self.client.loop_stop()

    def publish(self, topic, message):
        self.client.publish(topic, message)
    
    def subscribe(self, topic):
        self.client.subscribe(topic)

    def on_connect(self, client, userdata, flags, rc):
        self.conn_flag = True
        print('Connected to MQTT broker', self.conn_flag)

    def on_log(self, client, userdata, level, buf):
        #print('Log buffer', buf)
        pass

    def on_disconnect(self, client, userdata, rc):
        print('Disconnected from MQTT broker')

def main():
        mqttClient = MQTT(mqtt_ip).connect().start()
        topic = 'cd44558bb2454746a9a7c6b8c1fd4716/data'
        # integer = 1.0
        # ret = {
        #     "cadence": integer+0.1,
        #     "calories": integer+0.1,
        #     "distance": integer+0.1,
        #     "pace": integer+0.1,
        #     "power": integer+0.1,
        #     "strokes": integer+0.1,
        #     "timestamp": integer+0.1,
        #     "workoutTime": integer+0.1
        #     }
        # message = json.dumps(ret)
            
        # mqttClient.publish(topic, message)
        # print('Published {message} to {topic}')

        for i in range(3,6):
            integer = float(i)
            ret = {
            "cadence": integer+0.1,
            "calories": integer+0.1,
            "distance": integer+0.1,
            "pace": integer+0.1,
            "power": integer+0.1,
            "strokes": None,
            # "strokes": integer+0.1,
            "timestamp": integer+0.1,
            "workoutTime": integer+0.1,
            "heartRate": integer+0.1,
            "rowingTime": integer+0.1,
            "interval": integer+0.1

            }
            message = json.dumps(ret)
            
            mqttClient.publish(topic, message)
            print('Published {message} to {topic}')
            time.sleep(2)
        mqttClient.stop()

if __name__ == "__main__":
    main()


# pace: 500mSplitTime
# workoutTime
# rowingTime
# heartRate
# interval
# cadence: strokesperminute

# ADD:
# heartRate
# interval
# rowingTime


# workoutTime = total duration since start of workout
# rowingTime = duration of rowing