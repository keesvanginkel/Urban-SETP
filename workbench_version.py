# Copied from Rotterdam.ipynb, version 21/8/2020, update 24/8

from classes import *
import copy
from collections import OrderedDict
import csv
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import os
#import ipywidgets as widgets
import pickle

from pdb import set_trace

def run_model_workbench(SLR,transient,Mayor,Housing_market,implementation_time,do_print=False):  
    
    #IMPORT MODEL
    from models import Rotty
    from run_model import run_model01 #import the model flow
    
    Model = Rotty #this can also be an argument of the function
    
    #IMPORT SURGELEVEL
    #load all SLR scenarios available as pickles
    allSLR_Scenario = SLR_Scenario_from_pickles(os.path.join("SLR_projections","Transients"))
    #and select the right one
    SLR_obj = [x for x in allSLR_Scenario if x.name.split('__')[0].split('_')[1] == SLR][0]
    
    SH_name = transient.split('\\')[-1].split('.')[0]
    SH_obj = SurgeHeight(SH_name)
    SH_obj.from_csv(transient)
    
    SurgeLevel = combine_SurgeLevel(SLR_obj,SH_obj) 
    
    #SurgeLevel = generate_SurgeLevel_new(SLR,transient)
    
    #Convert implementation time to format we can use
    implementation_time = (implementation_time,int(round(implementation_time*10/7,0)))
    
    experiment = run_model01(Rotty,SurgeLevel,Mayor,Implementation_time=implementation_time,do_print=False)
    
    def Average(lst): 
        return sum(lst) / len(lst) 
    
    Model = experiment.Model
    
    
    #ANALYSE THE OUTCOMES OF THE MODEL, AND EVALUATE TIPPING POINTS IN THE TIME SERIES.
    HP = Model.allResidentialArea[0]
    CC = Model.allResidentialArea[1]
    
    #Return the timeseries of the house price.
    HP_hp_t_obj = [x  if x > 0 else 0 for x in HP.house_price_t_objective] #set all values <0 to 0
    HP_hp_t_sub = [x  if x > 0 else 0 for x in HP.house_price_t_subjective]
    
    CC_hp_t_obj = [x  if x > 0 else 0 for x in CC.house_price_t_objective] #set all values <0 to 0
    CC_hp_t_sub = [x  if x > 0 else 0 for x in CC.house_price_t_subjective]
    
    #Also return the value of the timeseries in 2200
    HP_hp_2200_obj = HP_hp_t_obj[179]
    HP_hp_2200_sub = HP_hp_t_sub[179]
    CC_hp_2200_obj = CC_hp_t_obj[179]
    CC_hp_2200_sub = CC_hp_t_sub[179]
    
    #######################################################
    ##### DO TIPPING POINT ANALYSIS ON MODEL OUTCOMES #####
    #######################################################
    
    window = 4 #The size of the rolling window
    margin = 2 # The margin around the TP

    #Criteria
    c1 = 0.15
    c2 = 0.2e10 #variance
    c3 = 10 #percent
    experiment.create_Metrics()
    
    for M in experiment.allMetrics:
        M.create_statistics() #Create summary statistics for the metric(t)
        M.find_SETP_candidates(c1=c1,c2=c2,c3=c3,window=window,margin=margin) #Evaluate the three tipping point criteria
        M.select_SETPs(sign=-1)
           
    
        if not len(M.selected_SETPs) == 0: #only if it has any SETPs
            first_real = M.selected_SETPs[0] #the first real tipping point
            if not len(M.candidates_as_lists[3]) == 0: #only if any of these exist
                first_only_before = M.candidates_as_lists[3][0]
                M.first_SETP = min(first_real,first_only_before)
            else: #only the 'real tipping point list' has items:
                M.first_SETP = first_real
        elif not len(M.candidates_as_lists[3]) == 0: #but there is an example of 'only stable before'
            first_only_before = M.candidates_as_lists[3][0]
            M.first_SETP = first_only_before
        else: M.first_SETP = None #both types do not exist
    
    #Decide on which value to return using type of housing market (R0 or R1)
    if Housing_market == 'rational':
        HP_first_SETP = experiment.allMetrics[0].first_SETP
        CC_first_SETP = experiment.allMetrics[2].first_SETP
        HP_hp_2200 = HP_hp_2200_obj
        CC_hp_2200 = CC_hp_2200_obj
    elif Housing_market == 'boundedly_rational':
        HP_first_SETP = experiment.allMetrics[1].first_SETP
        CC_first_SETP = experiment.allMetrics[3].first_SETP
        HP_hp_2200 = HP_hp_2200_sub
        CC_hp_2200 = CC_hp_2200_sub
    
    if HP_first_SETP is None: 
        HP_first_SETP = 9999
    if CC_first_SETP is None: 
        CC_first_SETP = 9999
        
    
    return HP_hp_2200, CC_hp_2200_obj, CC_hp_2200_sub, HP_first_SETP, CC_first_SETP
    
def init_time(Model,time,do_print=False):
    """
    Initiate all variables that change over time for all relevant objects
    And matches all areas with flood protection objects
    
    Arguments:
        *Model* (Urban-SETP model object) : The model of the city
        *time* (list) : Timeseries of all years for which the model is to run
        
    Return:
        *Model* (Urban-SETP model object) : The model of the city with time initiated
    
    """
    for FloodProtection in Model.allFloodProtection:
        FloodProtection.init_time(time)             

    for Area in Model.allResidentialArea:
        Area.match_with_FloodProtection(Model.allFloodProtection) #ADD THE INFORMATION OF THE FLOOD PROTECTION STRUCTURES TO THE AREAS IT PROTECTS
        Area.init_time(time) #create all the variables that are manipulated over time
    
    if do_print:
        print('Time is initiated for all Flood protection and Residential Area objects')
    return Model

    
