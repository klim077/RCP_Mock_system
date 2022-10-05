import platform
import os

import requests
import base64
import json


# Consul configuration
consul_ip = '172.17.0.1'  # This is docker host IP
consul_port = 8500
consul_url = 'http://{ip}:{port}/v1/kv'.format(
    ip=consul_ip,
    port=consul_port,
)


# def getEnvVar(variable):
#     # First priority: Variable defined in environment
#     try:
#         tmp = os.environ[variable]
#     except KeyError as e:
#         tmp = None

#     if tmp:
#         print('{}={} found in environment.'.format(variable, tmp))
#         return tmp
#     else:
#         # Second priority: Variable defined in consul
#         print('{} not found in environment.'.format(variable))
#         url = '{url}/smartgym/gateway/env'.format(url=consul_url)
#         try:
#             res = requests.get(url).json()
#         except Exception as e:
#             return None
#         value = res[0]['Value']
#         decoded = base64.b64decode(value)
#         kv = json.loads(decoded)
#         try:
#             v = kv[variable]
#         except KeyError as e:
#             v = None
#         if v:
#             print('{}={} found in consul.'.format(variable, v))
#             return v

#     print('{} not found in consul.'.format(variable))
#     return None


system = platform.system()
if system == 'Linux':
    # MQTT configuration
    broker_address = 'mosquitto-bridge'
    broker_port = 1883

    # Backend Redis configuration that is no longer in use
    # Remove this once rower controller has been updated to use websockets
    try:
        redis_ip = os.environ['SERVER_IP']
    except Exception as e:
        redis_ip = 'localhost'
    try:
        redis_port = 16379
    except Exception as e:
        redis_port = 16379

    # Backend configuration
    # server_ip = getEnvVar('SERVER_IP')
    server_ip = '192.168.1.119'

    # Graylog configuration
    try:
        graylog_ip = os.environ['GRAYLOG_IP']
    except Exception as e:
        graylog_ip = '192.168.8.89'

    try:
        graylog_port = os.environ['GRAYLOG_PORT']
    except Exception as e:
        graylog_port = 12201

    # Orchestrator configuration
    # local_redis_ip = getEnvVar('LOCAL_REDIS_IP')
    local_redis_ip = 'redis'

    if not local_redis_ip:
        local_redis_ip = 'redis'
    # local_redis_port = getEnvVar('LOCAL_REDIS_PORT')
    local_redis_port = 6379
    if not local_redis_port:
        local_redis_port = 6379
    else:
        local_redis_port = int(local_redis_port)

    # Gateway location
    # gateway_location = getEnvVar('GATEWAY_LOCATION')
    gateway_location = 'SmartGymInABox'

    # API Key
    # api_key = getEnvVar('API_KEY')
