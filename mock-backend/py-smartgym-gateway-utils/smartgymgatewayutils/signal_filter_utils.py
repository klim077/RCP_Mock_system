class EWMA_filter():
    
    def __init__(
        self,
        a = 0.1
    ):
        self.a = a
        self.filtered = 0
        self.prev_filt = 0

    def ewma_update(self, x):

        """Returns the output of the EWMA filter for that particular input
        Parameters:
        argument1 (numerical): the next value to be filtered
        Returns:
        (numberical):Returning value
        """

        self.filtered = (1 - self.a) * self.prev_filt + self.a*x

        self.prev_filt = self.filtered

        return self.filtered

    def reset_filter(self):

        self.filtered = 0
        self.prev_filt = 0

    def offline_filter(self,signal, a = 0.1):

        """Returns the filtered version of the signal array
        Parameters:
        argument1 (list/array): Signal that is going to be filtered
        Returns:
        list:Returning value
        """

        self.a = a
        self.reset_filter()

        filt_sig = []
        for val in signal:
            filt_val = self.ewma_update(val)
            filt_sig.append(filt_val)

        return signal