from enum import Enum


class HandlerTypes(Enum):
    CONSOLE = (1,)
    FILE = (2,)
    GRAYLOG = 3
