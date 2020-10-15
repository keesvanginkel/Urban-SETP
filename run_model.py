"""
This script defines the consequtive steps in one model experiment
"""

from classes import *

#global vars (depreciated)
k = 0.2 
T_eq = 70

def run_model01(Model,SurgeLevel,Mayor,Implementation_time=(7,10),do_print=False):  
    """
    The algorithm describing all the steps in one model experiment
    
    Arguments:
        *Model* (Model object) : Model object describing the city
        *SurgeLevel* (SurgeLevel object) : The extreme water level per year
        *Mayor* (Mayor object) : The mayor for this experiment
        *Implementation_time* (tuple) : Implementation time of the large and small measures respectively 
            Tuple elements (int) : Time in years
        
    Returns:
        *Experiment* (Experiment) : Contains all input arguments including the development of the model over time
    
    """
    
    #DEFINE MEASURES THAT MANY MAYORS WILL USE
    #since 14/10/2020 they are defined in the experiment
    small = Measure_FloodProtection("Minor Dike Heightening", Implementation_time[0], 0.5)
    large = Measure_FloodProtection("Major Dike Heightening", Implementation_time[1], 1)
    Measures = (small,large)
    
    #REMOVE ALL ACTIVE MEASURES FROM PREVIOUS RUNS
    allactiveMeasure.clear()
    
    time = SurgeLevel.years
    init_time(Model,time) #Initiate time for objects that have changing variables over time

    # THE MODEL RUNS OVER A YEARLY TIMESTEP
    for i,t in enumerate(time): #Iterate over the years t, with index i
        #print(i,t, end=" |")
        time_remaining = len(time) - i 
        
        for RA in Model.allResidentialArea:
            
            #FIRST EVALUATE IF THE FLOOD PROTECTION LEVEL IS EXCEEDED 
            if RA.protection_level[i] < SurgeLevel.surgelevel[i]: #if a flood occurs
                overtopping = SurgeLevel.surgelevel[i] - RA.protection_level[i]
                if overtopping < RA.volume_constraint_threshold: #constrain volume if overtopping < threshold
                      volume_attenuation_factor = overtopping / RA.volume_constraint_threshold
                else: volume_attenuation_factor = 1
                
                #water depth upon inundation is constrained by the volume_attenuation_factor
                RA.flood_history[i] = (SurgeLevel.surgelevel[i] - RA.elevation)*volume_attenuation_factor
                
                RA.flood_damage[i] = RA.calculate_damage(RA.flood_history[i],i)
                #print("Damage is calculated at: {} euro".format(dam))
                
                RA.event_history[i] = "~"
            
            #AND EVALUATE IF ANY NEAR MISS MIGHT HAVE OCCURED
            if 0 < RA.protection_level[i] - SurgeLevel.surgelevel[i] <= 0.5: #Near miss
                RA.nearmiss_history[i] = RA.protection_level[i] - SurgeLevel.surgelevel[i]
                
                RA.event_history[i] = "!"
            
            #THEN EVALUATE THE IMPACT ON TRUST #DEPRECIATED, TO BE REPLACE WITH BAYESIAN STUFF
            if i != 0: #don't evaluate trust in the first timestep!
                #print(RA.protection_level-levels_t[i])
                RA.event_impact_history[i] = evaluate_event(SurgeLevel.surgelevel[i]-RA.protection_level[i],
                                                              Model.Parameters['alarming_conditions'],False)
                #First evaluate the impact of this year's event (if any)
                RA.trust_t[i] = RA.trust_t[i-1] - RA.event_impact_history[i]

                #ALWAYS MODEL RECOVERY OF TRUST
                dTdt = (RA.trust_t[i]-T_eq)*-k
                RA.trust_t[i] = RA.trust_t[i] + dTdt

        
        for RA in Model.allResidentialArea:
            
            #CALCULATE THE OBJECTIVE RISK IN THE NEIGHBOURHOOD AND HOUSEHOLD IN THIS TIMESTEP 
            mu = Model.Parameters["Gumbel"]["mu"]
            beta = Model.Parameters["Gumbel"]["beta"]
            SLR = SurgeLevel.corresponding_SLR_Scenario.sealevel[i] #the degree of SLR in this timestep
            max_surge = RA.protection_level[i]-SLR #the maximum storm surge height this dike can cope with
            RA.protection_level_rp[i] = Gumbel_RP(max_surge,mu,beta) #Return period of the flood protection height
            RPs = [10000,5000,2000,1000,500,200,100,50,20,10,5,2]
            damages = [] #per neighborhood
            damages_household = []
            for RP in RPs:
                #Expected water levels are the sum of the Gumbel distributed WLs 
                waterlevel = Gumbel_inverse(RP,mu,beta) + SLR
                
                #Impose volume constraint
                overtopping = waterlevel - RA.protection_level[i]
                if overtopping < RA.volume_constraint_threshold: #constrain volume if overtopping < threshold
                      volume_attenuation_factor = overtopping / RA.volume_constraint_threshold
                else: volume_attenuation_factor = 1
                
                #Constrain the volume upon inundation
                inundation = (waterlevel - RA.elevation) * volume_attenuation_factor
                
                #Calculation per residential area
                damages.append(RA.calculate_damage(inundation,i)) #damage assuming no FPL
                
                #Calculation per household
                damages_household.append(RA.calculate_damage_household(inundation,i))
                    
            RA.risk[i] = risk_FP(damages.copy(),RPs.copy(),RA.protection_level_rp[i])*10**(-6) #EAD of Residential area in million 2010-euro's 
            RA.risk_household[i] = risk_FP(damages_household.copy(), RPs.copy(),RA.protection_level_rp[i]) #EAD [per household] in 2010-euros

            if time_remaining > RA.house_price_horizon:
                future_EADs = [RA.risk_household[i]] * RA.house_price_horizon #assume that all future damages equal current EAD
                RA.risk_household_discounted[i] = discount_risk(future_EADs,RA.r,RA.house_price_horizon)
                flood_discount = RA.risk_household_discounted[i] - RA.risk_household_discounted[0] # The increase in discounted risk
                #Calculate new house price
                RA.house_price_t_objective[i] = RA.house_price_0 - flood_discount #misschien niet helemala hetzelfde als Wouter heeft gedaan?
            
            #CALCULATE THE RISK PERCEPTION
            if i != 0: #skip in the first timestep (here the initial condition is used)
                #I_exp = 0; #the flood experience in the current timestep
                if RA.name == 'Area_A': #For the Heijplaat
                    RA.weigh_RP_Bayesian(i,Model.Parameters["I_experience_interp"],I_social=0) 
                elif RA.name == 'Area_B': #For the City Centre: account for risk perception in the Heijplaat
                    HP = Model.allResidentialArea[0]
                    RA.weigh_RP_Bayesian(i,Model.Parameters["I_experience_interp"],I_social=HP.risk_perception[i]) 
            
            RA.risk_perceived[i] = risk_FP(damages.copy(), #Copy of the damages
                                           shift_subjective_floods(RPs.copy(),RA.risk_perception[i]), #perceived return periods
                                           shift_subjective_floods(RA.protection_level_rp[i],RA.risk_perception[i]))*10**(-6) #return period of flood protection
            RA.risk_household_perceived[i] = risk_FP(damages_household.copy(), 
                                                     shift_subjective_floods(RPs.copy(),RA.risk_perception[i]), #perceived return periods
                                                     shift_subjective_floods(RA.protection_level_rp[i],RA.risk_perception[i])) #EAD [per household] in 2010-euros
            
            #TODO: ADD ANTICIPATE ON FUTURE SEA LEVEL RISE
            #Risk discounting: for now assume that households don't anticipate any sea level rise
            if time_remaining > RA.house_price_horizon:
                future_EADs_perceived = [RA.risk_household_perceived[i]] * RA.house_price_horizon #assume that all future damages equal current EAD
                RA.risk_household_discounted_perceived[i] = discount_risk(future_EADs_perceived,RA.r,RA.house_price_horizon)
                flood_discount_subjective = RA.risk_household_discounted_perceived[i] - RA.risk_household_discounted[0] # The increase in discounted risk
                #Calculate new house price
                RA.house_price_t_subjective[i] = RA.house_price_0 - flood_discount_subjective #misschien niet helemala hetzelfde als Wouter heeft gedaan?
            
            
            
        #IMPLEMENT FLOOD PROTECTION MEASURES
        Mayor.apply_strategy(Model,SurgeLevel,Measures,i,time)
        for measure in allactiveMeasure: #tell all measures that are currently planned that a timestep has passed and that their implementation is coming near 
            measure.countdown(i,len(time)) #we need to tell the measure instances which timestep it is
        
        for Area in Model.allResidentialArea: #kan naar hierboven! als method van measure
               RA.match_with_FloodProtection(Model.allFloodProtection)
    
    experiment = Experiment(Model,SurgeLevel,Mayor)
    
    if do_print:
        print("Finished experiment {}".format(experiment))
    
    return experiment

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

    for RA in Model.allResidentialArea:
        RA.match_with_FloodProtection(Model.allFloodProtection) #ADD THE INFORMATION OF THE FLOOD PROTECTION STRUCTURES TO THE AREAS IT PROTECTS
        RA.init_time(time) #create all the variables that are manipulated over time
    
    if do_print:
        print('Time is initiated for all Flood protection and Residential Area objects')
    return Model
