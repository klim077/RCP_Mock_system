import logging
import config
import graypy
import os

"""Logging Levels
|Level   |Numeric value|
|--------|-------------|
|CRITICAL|50           |
|ERROR   |40           |
|WARNING |30           |
|INFO    |20           |
|DEBUG   |10           |
|NOTSET  |0            |
"""


class LoggerWrapper:
    def __init__(self, name, level=logging.INFO):
        if not name:
            raise ValueError('Missing [name].')

        GATEWAY_LOCATION = config.gateway_location

        # Set up logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)

        logAdapter = logging.LoggerAdapter(logging.getLogger(__name__), {'project': 'SmartGym-demo'})

        # Configure formatter
        format_str = 'SmartGym/{location}/{service}/%(levelname)s:%(funcName)s:%(lineno)s:%(message)s'.format(
            location=GATEWAY_LOCATION, service=name)
        formatter = logging.Formatter(format_str)

        # Console logger
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # Graylog logger
        grayhandler = graypy.GELFUDPHandler(
            config.graylog_ip,
            config.graylog_port
        )
        grayhandler.setFormatter(formatter)
        self.logger.addHandler(grayhandler)

    def getLogger(self):
        return self.logger
