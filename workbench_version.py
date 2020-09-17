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

def run_model_workbench(SLR,transient,Mayor,do_print=False):  
    
    #IMPORT MODEL
    from models import Rotty
    from run_model import run_model01 #import the model flow
    
    Model = Rotty #this can also be an argument of the function
    
    #IMPORT SURGELEVEL
    SurgeLevel = generate_SurgeLevel_new(SLR,transient)
    
    experiment = run_model01(Rotty,SurgeLevel,Mayor,do_print)
    
    def Average(lst): 
        return sum(lst) / len(lst) 
    
    Model = experiment.Model
    
    Area_A_trust_2120 = Model.allResidentialArea[0].trust_t[99] #Trust Area_A in year 2120
    Area_B_trust_2120 = Model.allResidentialArea[1].trust_t[99] #Trust Area_B in year 2120
    Area_A_FPL2100to2120 = Average(experiment.Model.allResidentialArea[0].protection_level_rp[80:100]) #Protection level Area_A between 2100-2120
    Area_B_FPL2100to2120 = Average(experiment.Model.allResidentialArea[1].protection_level_rp[80:100]) #Protection level Area_A between 2100-2120
    
    return Area_A_trust_2120,Area_A_FPL2100to2120,Area_B_trust_2120,Area_B_FPL2100to2120

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

    
