from threading import Timer
from collections import deque

class PeriodicTask(object):

    def __init__(
            self,
            interval,
            callback,
            daemon=True,
            **kwargs,
            ):
        self.interval = interval
        self.callback = callback
        self.daemon = daemon
        self.kwargs = kwargs


    def run(self):
        
        if object is not None:
            print(**self.kwargs)
            self.callback(**self.kwargs)
            t = Timer(self.interval, self.run)
            t.daemon = self.daemon
            t.start()



