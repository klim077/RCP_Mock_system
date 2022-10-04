from collections import deque
import numpy as np

class ParameterQueue:

    def __init__(self, var_name, queue_max_size = 9999):

        self.currentVal = 0

        self.dataQueue = deque(maxlen = queue_max_size)
        self.var_name = var_name

    def updateCurrentVal(self, parameter_value) -> float:

        self.dataQueue.append(parameter_value)

    def getAvg(self) -> float:

        mean = np.mean(self.dataQueue)
        print(f'queue len: {len(self.dataQueue)})')
        if mean is None or np.isnan(mean):
            return 0.0
        return mean


    def clear(self):
        self.dataQueue.clear()
