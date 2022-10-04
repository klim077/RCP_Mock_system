

from . import signal_filter_utils

ewma_speed_filter = signal_filter_utils.EWMA_filter()

def fastest_time_taken_in_a_run(exercise,distance):
    fastest_time_taken = float('inf')
    distance_stack = []
    time_stack = []
    exercise_data = exercise["exercise_data"]
    speed_data = map(lambda x : x["distance"],exercise_data)
    speed_data = list(speed_data)
    filter_result = ewma_speed_filter.offline_filter(signal=speed_data)
    for x in range(len(filter_result)): 
        distance_stack.append(filter_result[x])
        time_stack.append(exercise_data[x]["workoutTime"])
        total_distance = sum(distance_stack)
        if(total_distance >= distance):
            time_taken = sum(time_stack)
            if(fastest_time_taken > time_taken):
                fastest_time_taken = time_taken
            while(total_distance >= distance):
                distance_stack.pop(0)
                time_stack.pop(0)
                total_distance = sum(distance_stack)

    return fastest_time_taken  

