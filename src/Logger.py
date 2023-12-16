from ._Logger.python import Logger as _Logger

class Logger(_Logger):
    def __init__(self, name: str):
        super().__init__(name)

logger = Logger('STF2CP')