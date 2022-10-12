class JetsonData:

    def __init__(
        self,
        timestamp,
        distance,
        cadence,
        calories,
        strokes,
        workoutTime,
        pace,
        power,
        rowingTime,
        interval,
        heartRate
    ):
        self.timestamp = timestamp
        self.distance = distance
        self.cadence = cadence
        self.calories = calories
        self.strokes = strokes
        self.workoutTime = workoutTime
        self.pace = pace
        self.power = power
        self.rowingTime = rowingTime
        self.interval = interval
        self.heartRate = heartRate

curr_raw = JetsonData(
                                    timestamp = 1.0,
                                    distance = 2.0,
                                    cadence = 3.0,
                                    calories = 4.0,
                                    strokes = 11.0,
                                    workoutTime = 5.0,
                                    pace = 6.0,
                                    power = 7.0,
                                    rowingTime = 8.0,
                                    heartRate = 9.0,
                                    interval = 10.0
                )

def handleNoneValues():
    attributes = [a for a in dir(curr_raw) if not a.startswith('__') and not callable(getattr(curr_raw, a))]
    for i in attributes:
        name = i
        print(name)
        if (getattr(curr_raw, name) == None):
            setattr(curr_raw, name, 0)
            print(getattr(curr_raw, name))

def main():
    print('running python scratch')
    handleNoneValues()

if __name__ == "__main__":
    main()