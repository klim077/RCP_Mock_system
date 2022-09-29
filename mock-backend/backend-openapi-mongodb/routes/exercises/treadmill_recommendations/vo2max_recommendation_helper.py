import pandas as pd
from datetime import datetime, timedelta

scoring_table = pd.read_csv("routes/exercises/treadmill_recommendations/2_4KmScoringTableforServiceMen.csv")
scoring_table.index = scoring_table["time"]
scoring_table.drop('time', axis=1, inplace=True)

score_group_time_dict = {}
for col in scoring_table:
    score_1_time = scoring_table[col][scoring_table[col] == 1].index.tolist()
    score_1_time = datetime.strptime(score_1_time[0],"%H:%M:%S")
    score_1_time = timedelta(hours=score_1_time.hour, minutes=score_1_time.minute, seconds=score_1_time.second)
    score_1_time = score_1_time.total_seconds()

    score_group_time_dict[int(col)] = score_1_time

def getTimeIpptRunScore1(age):
    '''
    Returns the time that would require a person to run 2.4Km and score 1 point 
    in the ippt run test
    '''

    ippt_grp = _convertAgeToIpptGroup(age)
    return score_group_time_dict[ippt_grp]

#IPPT Scoring Table Age Grouping:
def _convertAgeToIpptGroup(age: int) -> int:
    '''
    Returns the corresponding age group based on the IPPT run scoring table, 
    for a given age number in years.
    '''
    assert age >= 0, "Age must be greater than 0"
    
    if age < 22:
        return 1
    elif age <=24:
        return 2
    elif age <=27:
        return 3
    elif age <=30:
        return 4
    elif age <=33:
        return 5
    elif age <=36:
        return 6
    elif age <=39:
        return 7
    elif age <=42:
        return 8
    elif age <=45:
        return 9
    elif age <=48:
        return 10
    elif age <=51:
        return 11
    elif age <=54:
        return 12
    elif age <=57:
        return 13
    else:
        return 14


age_groups = {
              1: [20,29], 
              2: [30,39], 
              3: [40,49], 
              4: [50,59],
              5: [60,69],
              6: [70,79]
              }

vo2Max_percentiles= pd.DataFrame({
    1: [55.4,51.1,45.4,41.7],
    2: [54,48.3,44,40.5],
    3: [52.5,46.4,42.4,38.5],
    4: [48.9,43.4,39.2,35.6],
    5: [45.7,39.5,35.5,32.3],
    6: [42.1,36.7,32.3,29.4]
},
index=["95","80","60","40"])

def _getAgeGroup(age:int) -> int:

    assert age > 0, f"Age cannot be a negative integer"

    if age <= 29:
        return 1
    elif age <= 39:
        return 2      
    elif age < 49:
        return 3
    elif age < 59:
        return 4
    elif age < 69:
        return 5
    elif age < 99:
        return 6

def getVo2MaxLimit(age:int) -> float:

    age_group = _getAgeGroup(age)
    max_index = "95" #The 95th percentile will be the maximum recommended value

    return vo2Max_percentiles[age_group][max_index]

def time2Vo2Max(time: float) -> float:
    '''
    Estimated a Vo2Max estiamte based on run time

        Parameters:
            time (float): 2.4Km Run time in seconds
        Returns:
            vo2Max (float): Computed Vo2Max
    '''
    return 85.95 - ((3.079/60) * time)

def vo2Max2Time(vo2max):
    '''
    Estimates 2.4Km run time estiamte based on Vo2Max

        Parameters:
            vo2Max (float): Vo2Max value
        Returns:
            2_4_km_run_time (float): Estimate run time in seconds
    '''
    time_estimate = (85.95 - vo2max)/(3.079/60)

    return time_estimate