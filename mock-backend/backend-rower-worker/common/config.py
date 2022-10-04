import socket
from common import logger

# Variables
# try:
# If hostname resolves, then env is inside docker-compose
# socket.gethostbyname('redis')

logger.info('Loading docker-compose env')

redis_ip = 'redis'
redis_port = 6379

mongoapi_ip = 'openapi-mongodb'
mongoapi_port = 9090
# except:
#     # Else, fall back to docker-machine from host
#     logger.info('Loading docker-machine env')

#     # redis_ip = '192.168.99.101'
#     redis_ip = '127.0.0.1'
#     redis_port = 16379

#     # mongoapi_ip = '192.168.8.30'
#     mongoapi_ip = '127.0.0.1'
#     mongoapi_port = 22090

mongoapi_version = 'v0.1'
