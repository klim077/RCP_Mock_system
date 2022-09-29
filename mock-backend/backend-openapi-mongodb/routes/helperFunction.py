import pandas as pd
from src import mongoapi2
import json


def aggregate_by_time(exercise_list, freq):
    # Do aggregate in pandas because it is more straightforward than
    # mongoDB pipelines
    df = pd.DataFrame(exercise_list)
    tmp = df.groupby(
        pd.Grouper(
            key='exercise_started',
            freq=freq
        )
    ).sum()
    tmp.reset_index(inplace=True)  # make the index a column

    # Construct return value
    return {
        'user_nickname': exercise_list[0]['user_nickname'],
        'aggregateBy': freq,
        'data': tmp.to_dict('records'),
    }
