import os
import os.path
import json
import base64
import time


import requests
from fastapi.security import HTTPBasic
from fastapi import FastAPI, HTTPException, status


# from smartgymgatewayutils import config
# from smartgymgatewayutils import gwWorker
# from smartgymgatewayutils import gwConsul

import smartgymgatewayutils.config as config
import smartgymgatewayutils.gwWorker as gwWorker
# import smartgymgatewayutils.gwConsul as gwConsul


# Local config
RETRY_LIMIT = 3
RETRY_TIMEOUT = 1

# Get environment variables
SERVER_URL = config.server_url
GATEWAY_IP = config.gateway_ip
GATEWAY_LOCATION = config.gateway_location
CONSUL_IP = config.consul_ip
CONSUL_PORT = config.consul_port

# Register Consul service
SERVICE_NAME = 'phoneholder_service'
SERVICE_ADDRESS = 'phoneholder-service'
SERVICE_PORT = 16000

# gwConsul.registerService(
#     name=SERVICE_NAME,
#     address=SERVICE_ADDRESS,
#     port=SERVICE_PORT,
# )

# gwConsul.registerCheckHttp(
#     name=f'{SERVICE_NAME}_check_http',
#     service_id=SERVICE_NAME,
#     url=f'http://{GATEWAY_IP}:{SERVICE_PORT}/health',
# )


app = FastAPI(
    title="phoneholder service API",
    description="SmartGym API for smartphone holder service",
)


security = HTTPBasic()


# Healthcheck variables
HEALTHCHECK_COUNT = 0
HEALTHCHECK_LIMIT = 3


# @app.get("/healthcheck")
# def healthcheck():
#     global HEALTHCHECK_COUNT
#     if HEALTHCHECK_COUNT < HEALTHCHECK_LIMIT:
#         HEALTHCHECK_COUNT += 1
#         return {
#             "initialHealthcheckCount": HEALTHCHECK_COUNT,
#             "initialHealthcheckLimit": HEALTHCHECK_LIMIT,
#         }

#     url = f'http://{CONSUL_IP}:{CONSUL_PORT}/v1/health/checks/{SERVICE_NAME}'
#     res = requests.get(url=url)
#     res_json = res.json()[0]

#     if res_json['Status'] != 'passing':
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail=res_json
#         )

#     return res_json


@app.get("/fail")
def fail():
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail='Failure test'
    )


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def read_root():
    return get_by_location(GATEWAY_LOCATION)

# def get_docker_secret(secret_name):
#     try:
#         with open(f'/run/secrets/{secret_name}', 'r') as secret_file:
#             return secret_file.read().splitlines()[0]
#     except IOError:
#         raise

# @app.get("/wearable-auth")
# def get_wearable_auth_key():
#     return get_docker_secret('WEARABLE_AUTH_KEY')


@app.get("/{location}")
async def read_location(location: str):
    return get_by_location(location)


@app.get("/phs/here/")
def read_phs_here():
    return make_name_uuid_dict(read_root())


@app.get("/phs/{location}")
async def read_phs_location(location: str):
    return make_name_uuid_dict(await read_location(location))


def get_by_location(location):
    url = f'{SERVER_URL}/v0.1/machines/location/{location}'

    ret = None
    for i in range(RETRY_LIMIT):
        print(f'Attempt {i+1} of {RETRY_LIMIT}')
        try:
            ret = gwWorker.sendGetRequest(url=url)
            break
        except Exception as e:
            print(e)
            time.sleep(RETRY_TIMEOUT)

    # Check if ret is unassigned
    if ret is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable",
        )

    # Check status in response if any
    if ret is dict and 'status' in ret.keys() and ret['status'] >= 300:
        raise HTTPException(
            status_code=ret['status'],
            detail=ret,
        )

    return ret


def make_name_uuid_dict(uuids):
    return {uuid['name']: uuid['uuid'] for uuid in uuids}

@app.get("/machines/{machine_uuid}")
async def get_machines_info_by_id(machine_uuid: str):
    url = f'{SERVER_URL}/v0.1/machines/{machine_uuid}'

    ret = None
    for i in range(RETRY_LIMIT):
        print(f'Attempt {i+1} of {RETRY_LIMIT}')
        try:
            ret = gwWorker.sendGetRequest(url=url)
            break
        except Exception as e:
            print(e)
            time.sleep(RETRY_TIMEOUT)

    # Check if ret is unassigned
    if ret is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable",
        )

    # Check status in response if any
    if ret is dict and 'status' in ret.keys() and ret['status'] >= 300:
        raise HTTPException(
            status_code=ret['status'],
            detail=ret,
        )

    return ret