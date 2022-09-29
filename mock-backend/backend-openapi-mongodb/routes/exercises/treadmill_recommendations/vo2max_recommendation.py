import numpy as np
import pandas as pd
import math
from .met_helper.met_helper import METLookUp
from .vo2max_recommendation_helper import vo2Max_percentiles, getVo2MaxLimit, vo2Max2Time, getTimeIpptRunScore1


def riegelsTimeEstimation(t1: float, d1= 2.4, d2= 5.0, alpha=1.06) :
        '''
        Calculates an estimate of the time it would take to run a target distance (d2), based
        on a known time for a particular distnace

                Parameters:
                        t1:
                        d1:
                        d2:
                Returns:
                        t2:
        '''

        return t1 * math.pow((d2/d1),alpha)

def getTempoRunTimeEstimate():
        pass

def vo2MaxRunIntensityRecommendation(time_2_4k,
                               vo2max,
                               user_age,
                               pc_increment = 0.05,
                               ):
        '''
        Returns a recommendation for the intensity level of a NSFIT run.

                Parameters:
                        time_2_4k (float): 2.4Km run time in minutes
                        user_age (int): Age in years
                        pc_increment: Much much to increase the intensity

                Returns:
                        recommended_met_sec (float): Computed recommended intensity value
        '''

        vo2max_lim = getVo2MaxLimit(user_age)
        print(f"Vo2Max limite {vo2max_lim}")

        if vo2max == None or time_2_4k == None:
                t_target = getTimeIpptRunScore1(user_age)
        elif vo2max:
                if vo2max >= vo2max_lim:
                        print("Vo2Max is already at it's max")
                        t_target = vo2Max2Time(vo2max_lim)
                else:
                        #Set a 5% faster target running time 
                        t_target = time_2_4k * (1 - pc_increment)

        print(f't_target time is: {t_target}')
        d2 = 5.0 #5Km, to get the pace for a 5Km run
        t2 = riegelsTimeEstimation(t1=t_target,d1=2.4,d2=d2)
        speed_5k_kmH = d2/(t2/60/60)
        print(f'speed {speed_5k_kmH}')
        #Tempo run time intensity
        tempo_run_time_sec = 20 * 60
        met_sec = METLookUp(speed_5k_kmH, 0) * tempo_run_time_sec
        print(f'met_sec: {met_sec}')
        return met_sec
    
