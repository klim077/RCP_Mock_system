import consul


from . import config
from . import logger


# Variables
CONSUL_IP = config.consul_ip
CONSUL_PORT = config.consul_port


def client():
    '''Get a Consul client

    Args:
        Nothing
    Returns:
        Consul client
    '''
    logger.info(f'gwConsul client() start')

    return consul.Consul(CONSUL_IP, CONSUL_PORT)


def registerService(name: str, address: str, port: int, tags: list = []):
    '''Registers a consul service

    Args:
        name (str): Name of service
        address (str): Address of service
        port (int): Port of service
        tags (list): List of string tags
    Returns:
        Nothing
    '''
    logger.info(f"gwConsul register({name}, {address}, {port}, {tags}) start")

    # Register the service
    client().agent.service.register(
        name=name,
        address=address,
        port=port,
        tags=tags,
    )

    logger.info(f"gwConsul register({name}, {address}, {port}, {tags}) end")


def getServices() -> dict:
    '''Get a dict of all services

    Args:
        Nothing
    Returns:
        dict: Services
    '''
    logger.info(f'gwConsul getServices() start')

    return client().agent.services()


def getPort(name: str) -> int:
    '''Get service port

    Args:
        name (str): Name of service
    Returns:
        int: Port of service
    '''
    logger.info(f"gwConsul getPort({name}) start")

    # Get all services
    services = client().agent.services()

    # Check if service exists
    if name not in services.keys():
        return -1

    return services[name]['Port']


def getAddress(name: str) -> str:
    '''Get service address

    Args:
        name (str): Name of service
    Returns:
        str: Address of service
    '''
    logger.info(f"gwConsul getAddress({name}) start")

    # Get all services
    services = client().agent.services()

    # Check if service exists
    if name not in services.keys():
        return -1

    return services[name]['Address']


def registerCheckHttp(
    name: str,
    service_id: str,
    url: str,
    interval: str = '10s',
    timeout: str = '1s',
):
    '''Register a HTTP check

    Args:
        name (str): Name of check
        service_id (str): Name of service
        url (str): Full HTTP url to check
        interval (str): Defaults to '10s'
        timeout (str): Defaults to '1s'
    Returns:
        Nothing
    '''
    logger.info(
        f"gwConsul registerCheckHttp({name}, {service_id}, {url}, {interval}, {timeout}) start")

    # Register a HTTP check
    client().agent.check.register(
        name=name,
        service_id=service_id,
        check=consul.Check.http(
            url=url,
            interval=interval,
            timeout=timeout,
        ),
    )


def registerCheckTtl(
    name: str,
    service_id: str,
    ttl: str = '10s',
):
    '''Register a TTL check

    Args:
        name (str): Name of check
        service_id (str): Name of service
        ttl (str): Time to live. Defaults to '10s'
    Returns:
        Nothing
    '''
    logger.info(
        f"gwConsul registerCheckTtl({name}, {service_id}, {ttl}) start")

    # Register a TTL check
    self.c.agent.check.register(
        name=name,
        service_id=service_id,
        check=consul.Check.ttl(
            ttl=ttl,
        ),
    )


def registerCheckTcp(
    name: str,
    service_id: str,
    host: str,
    port: int,
    interval: str = '10s',
):
    '''Register a TCP check

    Args:
        name (str): Name of check
        service_id (str): Name of service
        host (str): Host IP
        port (int): Host port
        interval (str): Defaults to '10s'
    Returns:
        Nothing
    '''
    logger.info(
        f"gwConsul registerCheckTcp({name}, {service_id}, {host}, {port}, {interval}) start")

    # Register a TCP check
    self.c.agent.check.register(
        name=name,
        service_id=service_id,
        check=consul.Check.tcp(
            host=host,
            port=port,
            interval=interval,
        ),
    )


def sendTtl(check_id: str):
    '''Send TTL to Consul

    Args:
        check_id (str): Name of service
    Returns:
        Nothing
    '''
    logger.info(f"gwConsul sendTtl({check_id}) start")

    client().agent.check.ttl_pass(check_id=check_id)

    logger.info(f"gwConsul sendTtl({check_id}) end")
