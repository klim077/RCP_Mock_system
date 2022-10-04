import logging

from celery.signals import setup_logging

from .handler_factory import HandlerFactory
from .handler_types import HandlerTypes


def get_default_logger() -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # check to see if handlers have already been added
    # for example if init is being called multiple times
    if not logger.handlers:
        handler_factory = HandlerFactory()

        # write to stdout and graylog by default
        default_stdout_handler = handler_factory.get_handler(
            HandlerTypes.CONSOLE, logging.INFO
        )
        logger.addHandler(default_stdout_handler)

        default_graylog_handler = handler_factory.get_handler(
            HandlerTypes.GRAYLOG, logging.WARN
        )
        logger.addHandler(default_graylog_handler)

    return logger


@setup_logging.connect()
def override_celery_logger(*args, **kwargs):
    logger = get_default_logger()
    logger.info("celery logger suppressed, using custom logger")
    return logger
