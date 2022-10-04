# Python package for SmartGym Gateway

This a a Python package for services in the SmartGym Gateway.

Consists:

- config
- gwAvailability
- gwLogger
- gwHTTP
- gwMQTT
- gwOrchestrator
- gwSocketio
- gwRedis

---

## *** **Important** *** Set up git hooks

Set up git hooks to ensure build numbers are automatically incremented.
```bash
# Set up git hooks
make init
```
 
---

## Quick Start

This section explains how to use SmartGym Gateway Package.

### Install

Add this git repo into `requirements.txt`.

```bash
# requirement.txt

git+https://git.siotgov.tech/SmartGym/py-smartgym-gateway-utils.git
```

### Usage

Import and configure the logger first. The same logger is used by all the other modules in this package, as well as the controller that imports this package.

```python
# controller.py

from smartgymgatewayutils import logger, loggerWrapper

# Get hostname
hostname = os.environ['HOSTNAME']

# Configure logger
loggerWrapper.start('weightstack_{}'.format(hostname))

# Start logging
logger.info('Weightstack logger ready')
```

Import and start using other modules.

```python
# controller.py

# gwHTTP
from smartgymgatewayutils import gwHTTP
data = gwHTTP.httpGet(url)
ret = gwHTTP.httpPost(url=url, data=data)

# gwMQTT
from smartgymgatewayutils import gwMQTT
mqtt_client = gwMQTT.MQTTWrapper(mqtt_uuid)

# gwOrchestrator
from smartgymgatewayutils import gwOrchestrator
machineID = gwOrchestrator.acquireMachineId(
    ip=redis_ip_local,
    port=redis_port_local,
    hostname=hostname,
    machine_type=topic_name,
)

# gwSocketIO
from smartgymgatewayutils import gwSocketIO
gwSocketIO.sio.emit('message', y)

# gwAvailability
from smartgymgatewayutils import gwAvailability
gwAvailability.run()
gwAvailability.setFutureEvent(machineID)
gwAvailability.setUnavailable(machineID)
```
