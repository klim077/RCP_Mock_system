
import os
import pandas as pd


# file_path = os.path.join(os.path.dirname('met_helper'),
#                             'MET_lookup_table',
#                             "20200503_lookup.csv") 

file_path = 'routes/exercises/treadmill_recommendations/met_helper/MET_lookup_table/20200503_lookup.csv'

lookup = pd.read_csv(file_path, index_col=0)

lookup.columns = lookup.columns.astype(float) #grad_list
grad_list = lookup.columns

speed_list = lookup.index #speed_list
speed_list = speed_list.astype(float)

def METLookUp(speed, grad):
    
    lookup_col = min(grad_list, key=lambda x:abs(x-grad))
    lookup_index =  min(speed_list, key=lambda x:abs(x-speed))
    
    MET = lookup.loc[lookup_index, lookup_col]
    print("Speed {}, GRAD {} MET {}".format(speed, grad, MET))
    
    return MET