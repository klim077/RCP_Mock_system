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


# def getEnvVar(variable, default=None):
#     # First priority: Variable defined in environment
#     tmp = os.getenv(variable, None)
#     if tmp:
#         print(f'{variable}={tmp} found in environment.')
#         return tmp
#     print(f'{variable} not found in environment.')

#     # Second priority: Variable defined as consul env-json
#     url = f'{consul_url}/smartgym/gateway/env'
#     try:
#         res = requests.get(url).json()
#         value = res[0]['Value']
#         decoded = base64.b64decode(value)
#         kv = json.loads(decoded)
#         v = kv[variable]
#         if v:
#             print(f'{variable}={v} found in consul env-json.')
#             return v
#     except Exception as e:
#         print(f'{variable} encountered {type(e)}, not found in consul env-json.')

#     # Third priority: Variable defined as consul key-value pair
#     url = f'{consul_url}/smartgym/gateway/env/{variable}'
#     try:
#         res = requests.get(url).json()
#         value = res[0]['Value']
#         decoded = base64.b64decode(value)
#         decoded_str = decoded.decode()
#         if decoded_str:
#             print(f'{variable}={decoded_str} found in consul key-value.')
#             return decoded_str 
#     except Exception as e:
#         print(f'{variable} encountered {type(e)}, not found in consul key-value.')

#     # Fourth priority: Variable in docker secret
#     try:
#         with open(f'/run/secrets/{variable}', 'r') as secret_file:
#             secret = secret_file.read().splitlines()[0]
#         if secret:
#             print(f'{variable} found in docker secret.')
#             return secret
#     except IOError as e:
#         print(f'{variable} encountered {type(e)}, not found in docker secret.')

#     print(f'{variable} not found. Returning as {default}')
#     return default


system = platform.system()
if system == 'Linux':
    # MQTT configuration
    broker_address = 'mosquitto-bridge'
    broker_port = 1883

    # Backend configuration
    # server_ip = getEnvVar('SERVER_IP', 'smartgym.siotgov.tech')
    server_ip ='192.168.1.119:22090'
    # server_ip ='localhost:22090'
    # server_ip = '192.168.1.102:22090'       # MUST BE IP ADDRESS, CANNOT BE 'localhost'

    # Graylog configuration
    # graylog_ip = getEnvVar('GRAYLOG_IP', 'graylog.siotgov.tech')
    # graylog_port = int(getEnvVar('GRAYLOG_PORT', 10501))
    graylog_ip = 'graylog.siotgov.tech'
    graylog_port = 10501

    # Orchestrator configuration
    # local_redis_ip = getEnvVar('LOCAL_REDIS_IP', 'redis')
    # local_redis_port = int(getEnvVar('LOCAL_REDIS_PORT', 6379))
    local_redis_ip = 'redis'
    local_redis_port = 6379

    # Gateway location
    # gateway_location = getEnvVar('GATEWAY_LOCATION')
    gateway_location = 'SmartGymInABox'

    # Gateway IP
    # gateway_ip = getEnvVar('GATEWAY_IP')
    # gateway_ip = '192.168.1.119'
    gateway_ip = 'localhost'

    # Project name
    # compose_project_name = getEnvVar('COMPOSE_PROJECT_NAME')
    compose_project_name = 'Gateway'

    # API Key
    # api_key = getEnvVar('API_KEY')

# protocol = getEnvVar('PROTOCOL', 'https://')
protocol = 'http://'
server_url = protocol + server_ip
