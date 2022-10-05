import time

import paho.mqtt.client as mqtt

from . import logger


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
        logger.info(f'on_connect: rc: {rc}')
        if rc == 0:
            logger.info(f'Connected to mosquitto')
            client.connected_flag = True
            try:
                self.subscribe(self.topic)
            except:
                print("no topic set")
        else:
            logger.error('connection refused')
            raise Exception('connection refused')

    def on_message(self, client, userdata, message):
        len_before = len(self.msg)
        self.msg.append(message.payload.decode())
        logger.info(
            f'Message received, buffer length increased from {len_before} to {len(self.msg)}')
        logger.debug(f'on_message: received {self.msg}')

    def on_disconnect(self, client, userdata, rc):
        logger.info("disconnecting reason  " + str(rc))
        client.connected_flag = False
        self.setup(self.ip, self.port)

    def subscribeMqtt(self, topic):
        self.topic = topic
        self.subscribe(self.topic)

    def setup(self, ip, port, keepalive=60):
        logger.info(f'Setup MQTT with {ip}:{port}')
        self.ip = ip
        self.port = port
        mqtt_connect = False
        while not mqtt_connect:
            try:
                self.connect(self.ip, self.port, keepalive)
                mqtt_connect = True
                self.loop_start()  # Starts a threaded network loop, handles reconnections
                logger.info(f'Setup successful')
            except ConnectionRefusedError as e:
                logger.error(e)
                time.sleep(1)
        self.msg = []

    def next(self, blocking_time=1 / 2000):
        time.sleep(0.1)
        if len(self.msg) > 0:
            len_before = len(self.msg)
            msg = self.msg.pop(0)
            logger.info(
                f'Buffer length reduced from {len_before} to {len(self.msg)}')
            return msg, True
        else:
            return '-1', False
