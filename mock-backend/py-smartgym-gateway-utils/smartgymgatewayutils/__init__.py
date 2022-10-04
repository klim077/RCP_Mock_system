import pkg_resources  # part of setuptools

from . import config
from . import gwLogger

loggerWrapper = gwLogger.LoggerWrapper()
logger = loggerWrapper.logger

packageName = "smartgymgatewayutils"
__version__ = pkg_resources.require(packageName)[0].version
print(f'{packageName} version: {__version__}')
