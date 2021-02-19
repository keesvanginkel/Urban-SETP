### THIS SCRIPT IS MEANT FOR TESTING THE MODEL RUNS FOR ROTTY, OUTSIDE JUPYTER
### MEANT FOR BUGFIXING AND TESTING, AND NON-JUPYTER USERS

from pathlib import Path
from models import Rotty
from mayors import *

print("Loading model:")
print(Rotty)
print("-"*40)


print("Loading storm surge scenarios:")
# Load all SLR_Scenario
allSLR_Scenario = SLR_Scenario_from_pickles(Path('SLR_projections', 'Transients'))

# Load all SurgeHeight (Realisations of extreme value distribution)
for filename in Path('SurgeHeight', 'biased_from_five_hundred').glob('*.csv'):
    obj = SurgeHeight(filename.stem)  # Init object with name derived from filename
    obj.from_csv(filename)  # Fill the object with data from the csv file

# Create SurgeLevels by summing combinations of SLR_Scenario and SurgeHeights
for SLR_Scenario in allSLR_Scenario:
    for SurgeHeight in allSurgeHeight:
        combine_SurgeLevel(SLR_Scenario, SurgeHeight)

print("Loaded {} SLR Scenarios, namely:".format(len(allSLR_Scenario)))
for SLR_Scenario in allSLR_Scenario:
    print(SLR_Scenario.name,end=' ||| ')

print("Also loaded {} Surge Height scenarios".format(len(allSurgeHeight)))
print("Combined these to {} SurgeLevel scenarios".format(len(allSurgeLevel)))

print("Start making selection of these SurgeLevel scenarios")
transient = "five_hundred_8"
selection = [x for x in allSurgeLevel if x.name.split("__")[1] == transient] #only run experiments for one of the transients
selected_scens = ['01','03','05','09']
selection =  [x for x in selection if x.name.split('__')[0].split('_')[1] in selected_scens]
print("{} SurgeLevel scenarios were selected".format(len(selection)))

allMayors = [Reactive(),Economicus(),Sentiment(),Lawkeeper()]
print("Loaded the following Management strategies")
for Mayor in allMayors: print(Mayor.paper_name(),end=" ")
print("\n")

#Possible implementation_times
Implementation_times = [ #small measure, large measure
    (4,6),
    (5,7),
    (6,9),
    (7,10), #default
    (8,11),
    (9,13),
    (10,14),
    (11,16),
    (12,17),
    (13,19),
    (14,20)]

it_sel = 3 #select the it_pairs from the list
Implementation_times[it_sel]
print("Set the implementation times for small and large measures to \
{} years respectively.".format(Implementation_times[it_sel]))

print("-"*40, end="\n")
print("Importing model run algorithm.")
from run_model import run_model01

mayor_sel = Reactive()
print("Start running the model with strategy {}".format(mayor_sel.paper_name()))
experiments = []
for SurgeLevel in selection:
    experiment = run_model01(Rotty,SurgeLevel,mayor_sel,Implementation_times[it_sel],do_print=True)
    experiments.append(experiment)
print('Experiments finished...')
