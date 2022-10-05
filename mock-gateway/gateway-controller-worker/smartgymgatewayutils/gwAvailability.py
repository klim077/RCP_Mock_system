import datetime
import time
import sched

from . import config
from . import gwHTTP
from . import logger


# Track last un-availability time
available_threshold_seconds = 10
last_unavailable = datetime.datetime.now()
thresh_unavailable = datetime.timedelta(
    seconds=available_threshold_seconds
)

s = sched.scheduler(time.time, time.sleep)

# Future set availability event object
futureEvent = None


def run():
    s.run(blocking=False)


def setAvailability(machineID, state):
    logger.info(f'setAvailability({machineID}, {state})')

    # Preparation
    url = '{}/v0.1/machines/{}/keyvalues/available'.format(
        config.server_url,
        machineID
    )
    data = {'value': int(state)}

    # Actual post
    ret = gwHTTP.httpPost(url, data)


def setAvailable(machineID):
    logger.info(f'setAvailable({machineID})')

    # Set available on backend server
    setAvailability(machineID, 1)


def setFutureEvent(machineID):
    logger.info(f'setFutureEvent({machineID})')
    global futureEvent
    futureEvent = s.enter(
        available_threshold_seconds,
        1,
        setAvailable,
        (machineID, )
    )


def setUnavailable(machineID):
    logger.info(f'setUnavailable({machineID})')

    # Set unavailable on backend server
    setAvailability(machineID, 0)

    # Cancel any previous events first
    global futureEvent
    try:
        s.cancel(futureEvent)
        logger.info(f'futureEvent canceled')
    except Exception as e:
        logger.error(e)

    # Schedule availability to be set in the future
    setFutureEvent(machineID)
