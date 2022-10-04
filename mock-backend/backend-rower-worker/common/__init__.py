import logging

# Set up logger
logger = logging.getLogger(__name__)
# logger.setLevel(logging.WARNING)
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)
# logger.setLevel(logging.ERROR)
ch = logging.StreamHandler()
format_str = '%(levelname)s:%(lineno)s:%(message)s'
formatter = logging.Formatter(format_str)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.info('Logger ready')