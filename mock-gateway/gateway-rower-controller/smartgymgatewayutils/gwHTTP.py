import json

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# from . import config
# from . import logger
# from . import gwLogger
import smartgymgatewayutils.config as config
from smartgymgatewayutils.gwLogger import logger

# loggerName = '{}_{}'.format('smartGymUtils', 'gwHTTP')
# gwLogger.loggerWrapper.start(loggerName)

# apiKey = config.api_key


def requests_retry_session(
    retries=100,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


# Create one shared session
httpSession = requests_retry_session()


def httpGet(url):
    '''Manages GET from http endpoints

    Args:
        url: Full url of endpoint
             (i.e. https://server-ip/version/resource/resourceid)

    Returns:
        object: Response from server in decoded JSON (i.e. list, dict)
    '''
    headers = {
        'Accept': 'application/json',
        # 'X-API-Key': config.api_key
    }

    ret = None
    try:
        logger.info(f'GET {url}')
        ret = httpSession.get(
            url,
            headers=headers
        )
        # Calling json() decodes the response into a matching python object
        ret = ret.json()
        logger.info(ret)
    except Exception as e:
        logger.error(e)

    return ret


def httpPost(url, data):
    '''Manages POST to http endpoints

    Args:
        url: Full url of endpoint
             (i.e. https://server-ip/version/resource/resourceid)
        data: JSON compatible structure to be sent. json.dumps(data) would be
              called.

    Returns:
        str: Response from server
    '''
    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
        # 'X-API-Key': config.api_key,
    }
    ret = None
    try:
        logger.info(f'POST {url}')
        logger.info(data)
        ret = httpSession.post(
            url,
            data=json.dumps(data),
            headers=headers
        )
        print("api key : {}".format(config.api_key))
        logger.info("config system : {}".format(config.system))
        logger.info(f'{ret.status_code}')
        ret = ret.json()
        logger.info(ret)
    except Exception as e:
        logger.error(e)

    return ret
