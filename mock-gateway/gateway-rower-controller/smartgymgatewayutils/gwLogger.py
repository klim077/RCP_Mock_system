import logging
import os

# import graypy

from . import config

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

certFile = "/certs/smartgym.cert"
keyFile = "/certs/smartgym.pem"

isFile_1 = os.path.exists(certFile)
isFile_2 = os.path.exists(keyFile)
class LoggerWrapper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.started = False

    def start(self, name, certfile=None, keyfile=None, level=logging.INFO):
        if not name:
            raise ValueError('Missing [name].')

        if self.started:
            self.logger.warning('Logger already started.')
            return

        self.started = True

        

        # Configure formatter
        format_str = 'SmartGym/{location}/{service}/%(levelname)s:%(funcName)s:%(lineno)s:%(message)s'.format(
            location=config.gateway_location,
            service=name
        )
        formatter = logging.Formatter(format_str)

        # Console logger
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # # Graylog logger
        # if(isFile_1 and isFile_2):
        #     grayhandler = graypy.GELFTLSHandler(
        #         'apps.siotgov.tech', port=10501, certfile=certFile, keyfile=keyFile
        #     )
        # else:
        #     grayhandler = graypy.GELFUDPHandler(
        #         config.graylog_ip,
        #         config.graylog_port
        #     )

        # self.logger.warning(config.graylog_ip+" Port: "+str(config.graylog_port))
        # grayhandler.makeSocket()
        # grayhandler.setFormatter(formatter)
        # self.logger.addHandler(grayhandler)

        self.logAdapter = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'project': 'SmartGym'}
        )
        
        # Set up logger
        self.logger.setLevel(logging.INFO)


    def info(self, message):
        self.logAdapter.info(message)

    def error(self, message):
        self.logAdapter.error(message)

loggerWrapper = LoggerWrapper()
logger = loggerWrapper.logger
