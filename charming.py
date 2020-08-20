# this is just to learn to work with pycharm.

from classes import *
import copy
from collections import OrderedDict
import csv
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import os
import pickle

### PROVIDE DAMAGE CURVES ###
# From Excel Huizinga et al. (2017) JRC Global flood-depth damage function Excel - tab MaxDamage-residential
# 2010 price levels, The Netherlands
MaxDamage_Residential = {
    'Building_based': {'Structure': 561, 'Content': 281, 'Total': 842},  # euro/m2
    'Land-use_based': 168,  # euro/m2
    'Object_based': 84175}  # euro/house?

# Tab Damage functions DamCurve_Residential_buildings
depth = [0, 0.5, 1, 1.5, 2, 3, 4, 5, 6]  # depth in meter
dam_frac = [0, 0.25, 0.4, 0.5, 0.6, 0.75, 0.85, 0.95, 1.00]  # damage fraction (-)

dam_pars = (MaxDamage_Residential['Land-use_based'], depth, dam_frac)  # all parameters for the damage assessment
print('provided damage curves')

### BUILT MODEL COMPONENTS ###
Rotty = Model('Rotty')  # Initiate the model class

# Add residential areas to the model
Rotty.add_ResidentialArea(
    ResidentialArea("Area_A", 3, 0.4, 1500, 750, 300000, dam_pars, ["No"], "Residential area A: the Heijplaat"))
Rotty.add_ResidentialArea(
    ResidentialArea("Area_B", -1, 25, 500000, 250000, 350000, dam_pars, ["Dike"], "Residential area B: City Centre"))

# Add flood protection objections to the model
Rotty.add_FloodProtection(FloodProtection("No", 3.5, False, "Region without flood protection"))
Rotty.add_FloodProtection(FloodProtection("Dike", 4.5, False, "Sea dike"))
print('Did built the model')

print('The real estate per ResidentialArea:')
for RA in Rotty.allResidentialArea:
    RA.residential_capital()

# SET BAYESIAN WEIGHTING FACTORS
Rotty.allResidentialArea[0].Bayesian_pars = Bayesian_pars(  # Heijplaat
    a=[1, 1, 0.1],  # NO FLOOD, NEAR MISS, FLOOD (in Heijplaat, Near miss is handled as no flood!)
    b=[0.04, 0.04, 1],  # Experience in current timestep
    c=[0, 0, 0],  # Social interactions (from other neighbourhoods)
    d=[0, 0, 0])  # Media/science

Rotty.allResidentialArea[1].Bayesian_pars = Bayesian_pars(  # City Centre
    a=[1, 0.1, 0.1],  # NO FLOOD, NEAR MISS, FLOOD
    b=[0.04, 0.5, 1],  # Experience in current timestep
    c=[0.04, 0.2, 0.1],  # Social interactions (from other neighbourhoods)
    d=[0, 0, 0])  # Media/science

### SET MODEL PARAMETERS ###
Rotty.add_Parameter("alarming_conditions",
                    OrderedDict({
                        # water depth above flood protection level, Name of event, reduction of trust if this happens.
                        1: ['Major flood', 40],
                        0: ['Small flood', 20],
                        -0.2: ['Near miss', 10],
                        -0.4: ['Major wake-up', 7],
                        -1: ['Minor wake-up', 5],
                        -10: ['Nothing happens', 0]}))

Rotty.add_Parameter("Gumbel",  # From Sterl et al. 2009
                    OrderedDict({  # parameter for the Gumbel distribution
                        "mu": 2.33,
                        "beta": 0.234}))

Rotty.add_Parameter("Bayesian_weighing_constants",  # Adapted from Haer et al. (2017)
                    OrderedDict({  # a is the weighting of the previous timestep for the new risk perception
                        "a_noflood": 1,  # previous timestep weighs heavily if no flood occurs
                        "a_flood": 0.1,  # times b !!! previous timestep weighs little in case of flood
                        "b_noflood": 0.04,  # flood experience in current timestep
                        "b_flood": 1,  # weighs heavily in case of a flood
                        "c": 0,  # neighbours (other agents)
                        "d": 0.2}))  # media

# Haer et al, 2017, p1982
Rotty.add_Parameter("I_experience_interp",  # Used for linear interp of the experience(Haer et al., 2017)
                    {"xp": [0, 0.5],  # water depth
                     "fp": [0, 1]})

# Rotty.add_Parameter("Trust",
#        OrderedDict({
#              "k" : 0.2,
#              "T_eq" : 70 }))
# global pars (for the development of Trust)
k = 0.2
T_eq = 70

### PRINT THE MODEL OBJECT RESULT ###
print('This is the model object:')

print(Rotty.__dict__)

### LOAD STORM SURGE SCENARIOS ###
# Load all SLR_Scenario
for filename in os.listdir("SLR_projections"):
    if filename.endswith(".csv"):
        obj = SLR_Scenario(filename.split('.')[0]) #Init object with name derived from filename
        obj.from_csv(os.path.join('SLR_projections',filename)) #Fill the object with data from the csv file
# Load all SurgeHeight (Realisations of extreme value distribution)
for filename in os.listdir("SurgeHeight"):
    if filename.endswith(".csv"):
        obj = SurgeHeight(filename.split('.')[0]) #Init object with name derived from filename
        obj.from_csv(os.path.join('SurgeHeight',filename)) #Fill the object with data from the csv file
# Create SurgeLevels by summing combinations of SLR_Scenario and SurgeHeights
for SLR_Scenario in allSLR_Scenario:
    for SurgeHeight in allSurgeHeight:
        combine_SurgeLevel(SLR_Scenario,SurgeHeight)