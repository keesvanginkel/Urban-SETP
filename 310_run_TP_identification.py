### Script to run and bugfix the TP identification algorithm outside the Notebooks
#Can for example used for debugging and improving the algorithm in PyCharm

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
input_path = "temp/experiments/experiment_selection_2021_1_19.p"
assert Path(input_path).exists()
experiments = pickle.load( open( input_path, "rb" ) )

############# SELECT INTERESTING EXPERIMENTS ###############
selection = sel_exp(experiments,SLR_scenarios='03',SurgeHeights='five_hundred_3',Mayors='Sentiment',ITs=(4,6))
experiment = selection[0]
print(experiment)

############ SET TP-IDENTIFICATION PARAMETERS ##############
window = 4 #The size of the rolling window
margin = 2 # The margin around the TP

#Criteria
c1 = 0.15 #fraction of change relative to house price at t0
c2 = 1.5e9 #variance
c3 = 10 #percent

experiment.create_Metrics()
M = experiment.allMetrics[3]
M.create_statistics(window=window) #Create summary statistics for the metric(t)
M.find_SETP_candidates(c1=c1,c2=c2,c3=c3,margin=margin)
M.select_SETPs(sign=-1,add_stable_before=True) #Also consider states which are only stable before as policy relevant

fig, ax = M.plot_SETPs(figsize=(13,8))

print('einde')

