import logging

from .handler_factory import HandlerFactory
from .handler_types import HandlerTypes


class SmartgymLoggerBuilder:
    def __init__(self) -> None:
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.handler_factory = HandlerFactory()

    def add_handler(
        self, handler_type: HandlerTypes, log_level: int, logfile_loc: str = ""
    ) -> None:
        if len(logfile_loc) > 0:
            handler = self.handler_factory.get_handler(
                handler_type, log_level, logfile_loc=logfile_loc
            )
        else:
            handler = self.handler_factory.get_handler(handler_type, log_level)
        self.logger.addHandler(handler)

    def get_logger(self) -> logging.Logger:
        return self.logger
