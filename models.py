"""
This script contains the different models, which can be cities of alternative representations of cities,
which can be explored

@author: Kees van Ginkel
github.com/keesvanginkel

"""

__author__ = '{Kees van Ginkel}'

from classes import *
import os
from collections import OrderedDict


########################################################
#### SOME MODEL PARAMETERS SHARED BY SEVERAL MODELS ####
########################################################

                ##### DAMAGE CURVES ####

#From Excel Huizinga et al. (2017) JRC Global flood-depth damage function Excel - tab MaxDamage-residential
#2010 price levels, The Netherlands
MaxDamage_Residential = { 
    'Building_based' : { 'Structure' : 561,  'Content' : 281,    'Total' : 842}, #euro/m2
    'Land-use_based' : 168, #euro/m2
    'Object_based' : 84175 }#euro/house? 

#Tab Damage functions DamCurve_Residential_buildings
depth = [0,0.5,1,1.5,2,3,4,5,6] #depth in meter
dam_frac = [0,0.25,0.4,0.5,0.6,0.75,0.85,0.95,1.00] #damage fraction (-)
dam_pars= (MaxDamage_Residential['Land-use_based'],depth,dam_frac) #all parameters for the damage assessment
dam_pars_household = (MaxDamage_Residential['Object_based'],depth,dam_frac)






##########################################################
####                  MODEL COLLECTION                ####
##########################################################






# .----------------.  .----------------.  .----------------.  .----------------.  .----------------. 
#| .--------------. || .--------------. || .--------------. || .--------------. || .--------------. |
#| |  _______     | || |     ____     | || |  _________   | || |  _________   | || |  ____  ____  | |
#| | |_   __ \    | || |   .'    `.   | || | |  _   _  |  | || | |  _   _  |  | || | |_  _||_  _| | |
#| |   | |__) |   | || |  /  .--.  \  | || | |_/ | | \_|  | || | |_/ | | \_|  | || |   \ \  / /   | |
#| |   |  __ /    | || |  | |    | |  | || |     | |      | || |     | |      | || |    \ \/ /    | |
#| |  _| |  \ \_  | || |  \  `--'  /  | || |    _| |_     | || |    _| |_     | || |    _|  |_    | |
#| | |____| |___| | || |   `.____.'   | || |   |_____|    | || |   |_____|    | || |   |______|   | |
#| |              | || |              | || |              | || |              | || |              | |
#| '--------------' || '--------------' || '--------------' || '--------------' || '--------------' |
# '----------------'  '----------------'  '----------------'  '----------------'  '----------------' 







#### MODEL ROTTY FIRST VERSION ####
Rotty = Model('Rotty') #Initiate the model class

#Add residential areas to the model
Rotty.add_ResidentialArea(ResidentialArea(
    name="Area_A",
    elevation=3, # [m]
    surface_area=0.4, # [km^2]
    inhabitants = 1500,
    nr_houses = 750,
    house_price_0 = 300e3, # euro, pricelevel of t=0
    dam_pars = dam_pars, #TODO: IN A NEXT VERSION, ADD AS PARAMETER
    dam_pars_household = dam_pars_household,
    protected_by = ["No"],
    description = "Residential area A: the Heijplaat"))
Rotty.add_ResidentialArea(ResidentialArea(
    name="Area_B",
    elevation=-1,
    surface_area = 25,
    inhabitants=500e3,
    nr_houses = 250e3,
    house_price_0 = 350e3,
    dam_pars=dam_pars,
    dam_pars_household = dam_pars_household,
    protected_by=["Dike"],
    description="Residential area B: City Centre"))

#Add flood protection objections to the model
Rotty.add_FloodProtection(FloodProtection("No",3.5,"Region without flood protection"))
Rotty.add_FloodProtection(FloodProtection("Dike",4.5,"Sea dike"))

#SET BAYESIAN WEIGHTING FACTORS
Rotty.allResidentialArea[0].Bayesian_pars = Bayesian_pars( #Heijplaat
    a=[1,1,0.1], #NO FLOOD, NEAR MISS, FLOOD (in Heijplaat, Near miss is handled as no flood!)
    b=[0.04,0.04,1], #Experience in current timestep
    c=[0,0,0]) #Social interactions through media

Rotty.allResidentialArea[1].Bayesian_pars = Bayesian_pars( #City Centre
    a=[1,0.1,0.1], #NO FLOOD, NEAR MISS, FLOOD
    b=[0.04,0.5,1], #Experience in current timestep
    c=[0.02,0.4,0] ) #Social interactions (from other neighbourhoods)

#IMPOSE VOLUME CONSTRAINT THRESHOLDS
#This constrains the inundation volume for small volumes of overtopping.
#For the indicated value, bath-tub inundation is assummed. For smaller overtopping values,
#The water depth is linearly interpolated
Rotty.allResidentialArea[0].volume_constraint_threshold = 0.1 #m
Rotty.allResidentialArea[1].volume_constraint_threshold = 1 #m

#SET MODEL PARAMETERS
Rotty.add_Parameter("Gumbel", #From Sterl et al. 2009
        OrderedDict({ #parameter for the Gumbel distribution
              "mu"   : 2.33,
              "beta" : 0.234}))

#Haer et al, 2017, p1982
Rotty.add_Parameter("I_experience_interp", #Used for linear interp of the experience(Haer et al., 2017)
        {"xp" : [0,0.5], #water depth
         "fp" : [0,1]})

Rotty.add_Parameter("I_social", #Indicate how heavily the experience from other RA's weights
        1) #The extent to which the experience on the Heijplaat impacts the exp on the CC.