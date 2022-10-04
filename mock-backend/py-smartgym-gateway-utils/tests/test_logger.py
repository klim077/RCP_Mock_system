from smartgymgatewayutils.logger import *

logger = override_celery_logger()
logger.warning("celery logger")

logger = get_default_logger()
logger.warning("default logger")