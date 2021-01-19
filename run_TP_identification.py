### Script to run and bugfix the TP identification algorithm outside the Notebooks

#What do I want to replicate?


from classes import *
#in classes, also tipping will be imported!

import matplotlib.pyplot as plt
import os
import pandas as pd
import pickle
import random
from pathlib import Path

from matplotlib import patches
from matplotlib.collections import PatchCollection

################### LOAD THE EXPERIMENTS ###################
input_path = "temp/experiments/experiment_selection_2020_11_4.p"
assert Path(input_path).exists()
experiments = pickle.load( open( input_path, "rb" ) )

############# SELECT INTERESTING EXPERIMENTS ###############
selection = sel_exp(experiments,SLR_scenarios='01',SurgeHeights='five_hundred_0',Mayors='Lawkeeper')
experiment = selection[0]
print(experiment)

############ SET TP-IDENTIFICATION PARAMETERS ##############
window = 4 #The size of the rolling window
margin = 2 # The margin around the TP

#Criteria
c1 = 0.15 #fraction of change relative to house price at t0
c2 = 2e9 #variance
c3 = 10 #percent

experiment.create_Metrics()
for M in experiment.allMetrics:
    M.create_statistics() #Create summary statistics for the metric(t)
    M.find_SETP_candidates(c1=c1,c2=c2,c3=c3, window=window,margin=margin)
    M.select_SETPs(sign=-1,add_stable_before=True) #Also consider states which are only stable before as policy relevant

for M in experiment.allMetrics:
    fig, ax = M.plot_SETPs(window=window,figsize=(13,8))


