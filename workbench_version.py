# Copied from Rotterdam.ipynb, verison 21/8/2020

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


def run_model_workbench(SurgeLevel,Mayor,do_print=False):  
    from models import Rotty
    #global pars (for the development of Trust) Will be removed 
    k = 0.2 
    T_eq = 70
    Model = Rotty
    
    #REMOVE ALL ACTIVE MEASURES FROM PREVIOUS RUNS
    allactiveMeasure.clear()
    
    time = SurgeLevel.years
    init_time(Model,time) #Initiate time for objects that have changing variables over time

    # THE MODEL RUNS OVER A YEARLY TIMESTEP
    for i,t in enumerate(time): #Iterate over the years t, with index i
        #print(i,t, end=" |")
        
        for Area in Model.allResidentialArea:
            
            #FIRST EVALUATE IF THE FLOOD PROTECTION LEVEL IS EXCEEDED 
            if Area.protection_level[i] < SurgeLevel.surgelevel[i]: #if a flood occurs; TODO EVALUATE FROM FLOOD_HISTORY
                Area.flood_history[i] = SurgeLevel.surgelevel[i] - Area.elevation #Can also be negative (no flood!)
                
                Area.flood_damage[i] = Area.calculate_damage(Area.flood_history[i],i)
                #print("Damage is calculated at: {} euro".format(dam))
            
            #AND EVALUATE IF ANY NEAR MISS MIGHT HAVE OCCURED
            if 0 < Area.protection_level[i] - SurgeLevel.surgelevel[i] <= 0.5: #Near miss
                Area.nearmiss_history[i] = Area.protection_level[i] - SurgeLevel.surgelevel[i]
            
            
            #THEN EVALUATE THE IMPACT ON TRUST #DEPRECIATED, TO BE REPLACE WITH BAYESIAN STUFF
            if i != 0: #don't evaluate trust in the first timestep!
                #print(Area.protection_level-levels_t[i])
                Area.event_impact_history[i] = evaluate_event(SurgeLevel.surgelevel[i]-Area.protection_level[i],
                                                              Model.Parameters['alarming_conditions'],False)
                #First evaluate the impact of this year's event (if any)
                Area.trust_t[i] = Area.trust_t[i-1] - Area.event_impact_history[i]

                #ALWAYS MODEL RECOVERY OF TRUST
                dTdt = (Area.trust_t[i]-T_eq)*-k
                Area.trust_t[i] = Area.trust_t[i] + dTdt

        
        for RA in Model.allResidentialArea:
            
            #CALCULATE THE OBJECTIVE RISK IN THIS TIMESTEP
            mu = Model.Parameters["Gumbel"]["mu"]
            beta = Model.Parameters["Gumbel"]["beta"]
            SLR = SurgeLevel.corresponding_SLR_Scenario.sealevel[i] #the degree of SLR in this timestep
            #SLR = relevant_TS.surgelevel[i] #todo change name to SLR to avoid confusion!!
            max_surge = RA.protection_level[i]-SLR #the maximum storm surge level this dike can cope with
            RA.protection_level_rp[i] = Gumbel_RP(max_surge,mu,beta) #Return period of the flood protection level
            RPs = [10000,5000,2000,1000,500,200,100,50,20,10,5,2]
            damages = []
            for RP in RPs:
                #Expected water levels are the sum of the Gumbel distributed WLs 
                waterlevel = Gumbel_inverse(RP,mu,beta) + SLR
                inundation = waterlevel - RA.elevation
                damages.append(RA.calculate_damage(inundation,i)) #damage assuming no FPL
            RA.risk[i] = risk_FP(damages.copy(),RPs.copy(),RA.protection_level_rp[i])*10**(-6) #EAD in million 2010-euro's 
            
            #CALCULATE THE RISK PERCEPTION
            if i != 0: #skip in the first timestep (here the initial condition is used)
                I_exp = 0; #the flood experience in the current timestep
                #RA.weigh_RP_Bayesian(i,Model.Parameters["Bayesian_weighing_constants"],Model.Parameters["I_experience_interp"])
                RA.weigh_RP_Bayesian(i,Model.Parameters["I_experience_interp"])
            
            RA.risk_perceived[i] = risk_FP(damages.copy(), #Copy of the damages
                                           shift_subjective_floods(RPs.copy(),RA.risk_perception[i]), #perceived return periods
                                           shift_subjective_floods(RA.protection_level_rp[i],RA.risk_perception[i]))*10**(-6) #return period of flood protection
                
        #IMPLEMENT FLOOD PROTECTION MEASURES
        Mayor.apply_strategy(Model,SurgeLevel,i,time)
        for measure in allactiveMeasure: #tell all measures that are currently planned that a timestep has passed and that their implementation is coming near 
            measure.countdown(i,len(time)) #we need to tell the measure instances which timestep it is
        
        for Area in Model.allResidentialArea: #kan naar hierboven! als method van measure
               Area.match_with_FloodProtection(Model.allFloodProtection)
    
    experiment = Experiment(Model,SurgeLevel,Mayor)
    
    if do_print:
        print("Finished experiment {}".format(experiment))
    
    def Average(lst): 
        return sum(lst) / len(lst) 
    
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

    
