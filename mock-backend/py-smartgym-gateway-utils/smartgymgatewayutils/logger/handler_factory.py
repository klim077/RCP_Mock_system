import logging
import os
import graypy

from .handler_types import HandlerTypes

FORMAT_STRING = "[%(asctime)s] - %(levelname)s @ module:%(module)s function:%(funcName)s line:%(lineno)d | %(message)s"
DEFAULT_LOGFILE_LOC = "output.log"


class HandlerFactory:
    def __init__(self) -> None:
        self.formatter = logging.Formatter(FORMAT_STRING)

    def get_handler(
        self,
        handler_type: HandlerTypes,
        log_level: int,
        logfile_loc: str = DEFAULT_LOGFILE_LOC,
    ) -> logging.Handler:
        match handler_type:
            case HandlerTypes.CONSOLE:
                handler = logging.StreamHandler()
            case HandlerTypes.FILE:
                handler = logging.FileHandler(logfile_loc)
            case HandlerTypes.GRAYLOG:
                # check if keys exist
                certFile = "/certs/smartgym.cert"
                keyFile = "/certs/smartgym.pem"
                certfile_exists = os.path.exists(certFile)
                keyfile_exists = os.path.exists(keyFile)
                    
                # if keys exist use TLS, else UDP
                if (certfile_exists and keyfile_exists):
                    handler = graypy.GELFTLSHandler("apps.siotgov.tech", port=10501, certfile=certFile, keyfile=keyFile)
                else:
                    handler = graypy.GELFUDPHandler("192.168.8.89", 12201)
            case _:
                raise ValueError("handler type not implemented")

        handler.setLevel(log_level)
        handler.setFormatter(self.formatter)
        return handler
