import imp
import logging
import os
import time
import subprocess
import collections

# from smartgymgatewayutils import config
# from smartgymgatewayutils import gwRedis
# from smartgymgatewayutils import logger, loggerWrapper
import smartgymgatewayutils.config as config
import smartgymgatewayutils.gwRedis as gwRedis
from smartgymgatewayutils.gwLogger import logger, loggerWrapper
# Get hostname
hostname = os.environ['HOSTNAME']

# Prepare logger
loggerName = f'orchestrator_{hostname}'
loggerWrapper.start(loggerName, level=logging.DEBUG)
logger.info(f'{loggerName} logger ready')
logger.setLevel(logging.DEBUG)


def getList(client, name):
    '''Get members of a redis list.

    Args:
        client: Redis client
        key: Key of redis set

    Returns:
        set: Set of members in redis set
    '''
    ret = client.lrange(name, 0, -1)
    ret = [i.decode() for i in ret]

    return ret


def getSet(client, key) -> set:
    '''Get members of a redis set.

    Args:
        client: Redis client
        key: Key of redis set

    Returns:
        set: Set of members in redis set
    '''
    ret = client.smembers(key)
    ret = {i.decode() for i in ret}

    return ret


def splitSubmitted(value: str) -> dict:
    '''Splits a submitted string

    Args:
        value (str): machineID:machineType

    Returns:
        dict: {'machineID': x, 'machineType': y}
    '''

    machineID, machineType = value.split(':')

    # Sanitize variables
    machineID = machineID.strip()
    machineType = machineType.strip()

    return {
        'machineID': machineID,
        'machineType': machineType,
    }


def getSubmitted(client) -> list:
    submittedKey = 'submitted'

    submittedSet = getSet(client, submittedKey)

    return [splitSubmitted(i) for i in submittedSet]


def splitRequested(value: str) -> dict:
    '''Splits a requested string

    Args:
        value (str): containerID:machineType

    Returns:
        dict: {'containerID': x, 'machineType': y}
    '''

    containerID, machineType = value.split(':')

    return {
        'containerID': containerID,
        'machineType': machineType,
    }


def getRequestsKey():
    return 'orchestrator_queue'


def getRequests(
    client,
    expected: int,
    retries: int = 5,
    timeout: int = 3
) -> list:
    if not expected:
        logger.info(f'Expecting {expected} requests, returning')
        return []

    for i in range(retries):
        time.sleep(timeout)
        logger.info(f'Get requests attempt {i+1} of {retries}')

        requestedList = getList(client, getRequestsKey())
        received = len(requestedList)
        if received == expected:
            logger.info(f'Received expected {expected} requests')
            return [splitRequested(i) for i in requestedList]

        logger.info(f'Expected requests: {expected}, got {received}')

    logger.warning(f'Max retries reached, return with received')
    return [splitRequested(i) for i in requestedList]


def deleteKey(client, key: str):
    client.delete(key)


def clearRequests(client):
    logger.info('Clearing requests')
    deleteKey(client, getRequestsKey())


def runCommand(command):
    return subprocess.check_output(command, shell=True).decode()


def scaleService(serviceName: str, numDesired: int):
    logger.info(f'Scaling {serviceName} to {numDesired}')

    command = f'docker service scale {serviceName}={numDesired}'

    ret = runCommand(command)

    return ret


def forceRestart(service: str):
    logger.info(f'Force restarting {service}, this may take a while')

    command = f'docker service update {service} --force'

    ret = runCommand(command)

    return ret


def killContainer(nodeIP: str, containerID: str):
    '''Kill containerID in nodeIP

    Args:
        nodeIP (str): IP address of swarm node
        containerID (str): Container ID

    Returns:
        bool: Kill successful?
    '''
    logger.info(f'Killing {containerID} in {nodeIP}')
    command = f'./swarm-kill.sh {nodeIP} {containerID}'

    ret = runCommand(command).strip()
    logger.debug(f'swarm-kill return={ret}')

    return ret == containerID


def delContainers(containers: list):
    for container in containers:
        nodeIP = container['nodeIP']
        containerID = container['containerID']
        if killContainer(nodeIP, containerID):
            logger.info(f'Killed {containerID} in {nodeIP}')
        else:
            logger.info(f'Unable to kill {containerID} in {nodeIP}')


def getServices() -> list:
    command = 'docker service ls | grep "controller" | awk \'{print $2}\''
    ret = runCommand(command)

    # Post process
    retList = ret.split()

    return retList


def getServiceDict(invert=False):
    projectName = config.compose_project_name
    serviceDict = {
        'chestpress': f'{projectName}_weightstack-controller',
        'weightstack': f'{projectName}_weightstack-controller',
        'bike': f'{projectName}_bike-controller',
        'treadmill': f'{projectName}_treadmill-controller',
        'weighingscale': f'{projectName}_weighingscale-controller',
        'bodyweight': f'{projectName}_bodyweight-controller',
        'bpm': f'{projectName}_bpm-controller',
        'rower': f'{projectName}_rower-controller',

    }

    if invert:
        serviceDict = {v: k for k, v in serviceDict.items()}

    return serviceDict


def splitContainerInfo(value: str, service: str) -> dict:
    '''Splits a container info string

    Args:
        value (str): machineID:machineType:containerID:nodeIP

    Returns:
        dict: {'machineID': w, 'machineType': x, containerID': y, 'nodeIP': z}
    '''

    # Get inverted service dict
    invertedServiceDict = getServiceDict(invert=True)

    machineID, machineType, containerID, nodeIP = value.split(':')

    # Sanitize variables
    machineID = machineID.strip()
    machineType = machineType.strip()
    containerID = containerID.strip()
    nodeIP = nodeIP.strip()

    return {
        'machineID': machineID or None,
        'machineType': machineType or invertedServiceDict[service],
        'containerID': containerID,
        'nodeIP': nodeIP,
    }


def getContainerInfo(service: str) -> list:
    '''Gets container info for a service.

    Args:
        service (str): Name of service

    Returns:
        list: List of dict with machineID, machineType, containerID, nodeIP
    '''
    logger.info(f'Get container info for {service}')

    command = f'./swarm-exec.sh {service} bash -c \'echo -n "$(cat MACHINEID 2> /dev/null):$(cat MACHINETYPE 2> /dev/null):$HOSTNAME"\''
    ret = runCommand(command)
    logger.debug(f'{ret=}')

    # Post process
    retList = ret.strip().split('\n')
    retList = list(filter(None, retList))
    logger.debug(f'{retList=}')

    return [splitContainerInfo(i, service) for i in retList]


def getContainerState() -> list:
    state = []
    for svc in getServices():
        state += getContainerInfo(svc)

    return state


def subtract(a: list, b: list) -> list:
    '''Computes a minus b.

    Args:
        a (list): Left operant
        b (list); Right operant

    Returns:
        dict: Result of different
    '''

    aKey = [i['machineID'] for i in a]
    bKey = [i['machineID'] for i in b]

    # Takes a - b
    keys = set(aKey) - set(bKey)

    # Filters a for diff results
    return [i for i in a if i['machineID'] in keys]


def findMissing(desired: list, current: list) -> list:
    '''In desired, but not in current.

    Args:
        desired (list): of dict with machineID, machineType
        current (list): of dict with machineID, machineType, containerID, \
            nodeIP

    Returns:
        dict
    '''

    return subtract(desired, current)


def findExtra(desired: list, current: list) -> list:
    '''In current, but not in desired.

    Args:
        desired (list): of dict with machineID, machineType
        current (list): of dict with machineID, machineType, containerID, \
            nodeIP

    Returns:
        dict
    '''

    return subtract(current, desired)


def computeActions(desired: list, current: list) -> list:
    '''Compute actions to be taken based on desired state and current state.

    Args:
        desired (list): of dict with machineID, machineType
        current (list): of dict with machineID, machineType, containerID, \
            nodeIP

    Returns:
        list
    '''

    # Filter
    extraList = findExtra(desired, current)
    missingList = findMissing(desired, current)

    # Add action field
    extraList = [dict(i, **{'action': 'del'}) for i in extraList]
    missingList = [dict(i, **{'action': 'add'}) for i in missingList]

    return extraList + missingList


def sortByService(actions: list, desired: list) -> list:
    '''Sorts into a dict of service.
    Each service is a dict of serviceName, desired, add, and del.

    Args:
        actions (list): with action
        desired (list): with machineID, machineType

    Returns:
        list
    '''
    logger.info('Sorting by services')

    # Get service dict
    serviceDict = getServiceDict()

    ret = {k: collections.defaultdict(list) for k in serviceDict}

    for machineType, serviceName in serviceDict.items():
        ret[machineType]['serviceName'] = serviceName

    for item in desired:
        machineType = item['machineType']
        ret[machineType]['desired'].append(item)

    for item in actions:
        machineType = item['machineType']
        action = item['action']
        ret[machineType][action].append(item)

    ret = [v for k, v in ret.items()]

    logger.debug(f'sortedService={ret}')
    return ret


def applyActionToService(service: dict):
    '''Actions differ base on number of add and del tasks.

    | # |add|del| action                       |
    | - | - | - | -                            |
    | 1 | 0 | 0 | none                         |
    | 2 | 0 | N | scale down and force restart |
    | 3 | n | N | scale down and force restart |
    | 4 | N | 0 | scale up                     |
    | 5 | N | n | scale up and selective kill  |
    | 6 | N | N | selective kill               |

    Args:
        service (dict): Dict containing service actions
    '''

    numAdd = len(service['add'])
    numDel = len(service['del'])
    numDesired = len(service['desired'])
    serviceName = service['serviceName']
    toDel = service['del']

    logger.info(f'Applying actions to {serviceName}')

    # Case 1
    if numAdd == 0 and numDel == 0:
        logger.info('No actions needed')
        return

    # Case 2 & 3
    if numDel > numAdd:
        logger.info(
            f'Scale down {serviceName} to 0 first, then back up to {numDesired} in the next cycle')
        # Scale down to desired
        scaleService(serviceName, 0)
        return

    # Case 4
    if numAdd > 0 and numDel == 0:
        logger.info(f'Scale up {serviceName} to {numDesired}')
        # Scale up to desired
        scaleService(serviceName, numDesired)
        return

    # Case 5
    if numAdd > numDel:
        logger.info(
            f'Scale up {serviceName} to {numDesired} and kill {numDel} containers')
        # Scale up to desired
        scaleService(serviceName, numDesired)
        delContainers(toDel)
        return

    # Case 6
    if numAdd == numDel:
        logger.info(f'Kill {numDel} containers')
        delContainers(toDel)
        return


def applyActions(actions: list, desired: list):
    '''Sort services and apply action for each service

    Args:
        actions (list): of dict containing action field
    '''
    logger.info('Applying actions')

    for service in sortByService(actions, desired):
        applyActionToService(service)

    return


def filterAddActions(actions: list) -> list:
    '''Returns a list of machineID to be added

    Args:
        actions (list): of dict with action

    Returns:
        list: of dict with action 'add' only
    '''

    return [i for i in actions if i['action'] == 'add']


def matchRequests(requests: list, available: list) -> list:
    if not available:
        logger.info(f'Retrieving {len(available)} available, returning')
        return []

    if not requests:
        logger.info(f'Expecting {len(requests)} requests, returning')
        return []

    logger.info(
        f'Matching {len(requests)} requests to {len(available)} available')

    ret = []
    for request in requests:
        for idx, avail in enumerate(available):
            if request['machineType'] == avail['machineType']:
                break
        matched = available.pop(idx)
        ret.append(dict(request, **matched))
        logger.info(
            f"Matched container ID {request['containerID']} of machineType {request['machineType']} to machineID {matched['machineID']}")

    return ret


def serveRequests(client, serveList: list):
    if not serveList:
        logger.info(f'Receiving {len(serveList)} serves, returning')
        return

    for serve in serveList:
        containerID = serve['containerID']
        machineID = serve['machineID']
        client.lpush(containerID, machineID)


def main():
    logger.info('Start main')

    # Variables
    orchestration_timeout = 10

    # Connect to redis
    r = gwRedis.connect(
        config.local_redis_ip,
        config.local_redis_port
    )

    while True:
        try:
            # Timeout
            time.sleep(orchestration_timeout)

            # Take snapshot of submitted
            desiredList = getSubmitted(r)
            logger.debug(f'{desiredList=}')

            # Detect current state of containers
            currentList = getContainerState()
            logger.debug(f'{currentList=}')

            # Figure out actions needed
            actionList = computeActions(desiredList, currentList)
            logger.debug(f'{actionList=}')

            # Clear requests
            clearRequests(r)

            # Apply actions needed
            applyActions(actionList, desiredList)

            # Filter actions by add action
            availableList = filterAddActions(actionList)
            logger.debug(f'{availableList=}')

            # Get requests
            requestsList = getRequests(r, len(availableList))
            logger.debug(f'{requestsList=}')

            # Match requests from available
            serveList = matchRequests(requestsList, availableList)
            logger.debug(f'{serveList=}')

            # Serve requests
            serveRequests(r, serveList)

        except Exception as e:
            logger.error(e)


if __name__ == '__main__':
    main()
