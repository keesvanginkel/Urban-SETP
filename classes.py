import csv
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pickle
from abc import ABC, abstractmethod
from math import log, exp
from copy import deepcopy
from datetime import datetime

from pdb import set_trace


#TRACK THE OBJECTS THAT WERE INITIATED
allSurgeSeries = []
allSLR_Scenario = []
allSurgeHeight = []
allSurgeLevel = []

class Experiment():
    """An experiment object is a unique combination of (1) one model (a city), 
       (2) managed by a one mayor,
       (3) in one storm surge scenario
       containing all information of the objects AFTER running the model
       
       can OPTIONALLY: also have metrics
    """
    
    def __init__(self,Model,SurgeLevel,Mayor,name=None):
        self.Model = deepcopy(Model)
        self.SurgeLevel = deepcopy(SurgeLevel)
        self.Mayor = deepcopy(Mayor)
        self.time = datetime.now() #moment at which the experiment was saved 
        if name is None: #If experiment is not provided with a name, make one!
            self.name = "{}_{}_{}".format(Model.name,SurgeLevel.name,Mayor.get_name())
    
    def __repr__(self):
        return self.name + " " + self.time.strftime("%Y/%m/%d, %H:%M:%S")
    
    def create_Metrics(self):
        """
        Output metrics of interest
        In this version: the house prices
        
        Arguments:
            *metrics* (list) : list items contain all output parameters which are considered model metrics
        
        Returns:
            *df* (DataFrame) : Contains output metrics of interest, index=years
        """
        allMetrics = [] #List tracking all experiment metrics
        for RA in self.Model.allResidentialArea: #BETTER, ITEMS TO LOOP OVER OUTSIDE THE METHOD!
            allMetrics.append(Metric(data=RA.house_price_t_objective,
                                     index=self.SurgeLevel.years,
                                     name="{}_house_price_obj".format(RA.name)
                                     ))
            allMetrics.append(Metric(data=RA.house_price_t_subjective,
                                     index=self.SurgeLevel.years,
                                     name="{}_house_price_subj".format(RA.name)))     
        self.allMetrics = allMetrics
        return 
    
    def to_df(self):
        """
        Convenience function to export some key experiment variables to a pandas dataframe
        It iterates over the attributes of the different objects, and selects based on the values
        defined in the lists "object_include"


        Arguments:
            *self* (Experiment object) : can have metrics or not

        Returns:
            *df* (Pandas DataFrame)
        """
        Model = self.Model
        SurgeLevel = self.SurgeLevel
        Mayor = self.SurgeLevel

        df = pd.DataFrame(index=SurgeLevel.years)
        df['name'] = self.name

        #for attr, value in Model.__dict__.items():
        #    print(attr)
        SL_include = ['surgelevel']
        SL = SurgeLevel
        for attr, value in SL.__dict__.items():
            if str(attr) in SL_include:
                df["{}".format(attr)] = value

        FP_include = ['protection_level','measure_history']
        for FP in Model.allFloodProtection:
            name = FP.name
            if not name == 'No': #ignor the no
                for attr, value in FP.__dict__.items():
                    if str(attr) in FP_include:
                        df["{}_{}".format(name,attr)] = value

        RA_include = ['event_history','nearmiss_history','flood_damage','risk_household',
                      'risk_household_perceived','risk_household_discounted','risk_household_discounted_perceived',
                      'protection_level_rp','risk_perception','risk_perceived','house_price_t_subjective','house_price_t_objective']
        for RA in Model.allResidentialArea:
            name = RA.name
            for attr, value in RA.__dict__.items():
                #print(attr)
                if str(attr) in RA_include:
                    df["{}_{}".format(name,attr)] = value

        ### Todo: also include metrics

        return df
    
    
def save_experiments(experiments,path=None):
    """
    Saves a list of experiments to a pickle, so it can be reused
    
    Arguments:
        *experiments* (list) : List containing Experiment objects
        *path* (string) : Path to save pickle
    """
    import pickle
    from datetime import datetime
    
    #save in a default folder
    if not path:
        foldername = "temp"
        subfolder = "experiments"
        target = os.path.join(foldername,subfolder)
        
        today = datetime.date(datetime.now())
        date = "{}_{}_{}".format(today.year,today.month,today.day)
        
        if not os.path.exists(foldername):
            os.mkdir(foldername)
            if not os.path.exists(target):
                os.mkdir(target)
        path = os.path.join(target,"experiment_" + date + ".p")
    
    if os.path.exists(path):
        print('The destination file {} already exists!'.format(path))
        cont = input('Do you want to overwrite it? If so, type "y"\n If you type something else, it wont save.')
        if cont != 'y':
            return print("File not saved")
    
    pickle.dump(experiments, open( os.path.join(path), "wb") ) 
    return print("File saved at: {}".format(path))

def sel_exp(experiments,SLR_scenarios='All',SurgeHeights='All',Mayors='All'):
    """Filter a list of experiments, based on the inputs values
    
    Arguments:
        *experiments* (list of experiment objects) : The input experiments
        *SLR_scenario* (str/list of strs) : Number referring to the SLR scenario
        *SurgeHeight* (int or string / list of ints/strings) : Number referring to the transient storm surge height scenario
        *Mayor* (str/list of strs) : Name of the mayor(s)
    
    Returns:
        *selection* (list of experiment objects) : The selected experiments
    """
    selection = experiments
    
    
    if not SLR_scenarios == 'All':
        if isinstance(SLR_scenarios,str):
            SLR_scenarios = [SLR_scenarios] #put the value in a list
        SLR_scenarios = ['Scenario_' + name for name in SLR_scenarios]
        selection = [exp for exp in experiments if exp.SurgeLevel.corresponding_SLR_Scenario.name in SLR_scenarios]
    
    if not SurgeHeights == 'All':
        if not isinstance(SurgeHeights,list):
            SurgeHeights = [SurgeHeights]
        SurgeHeights = [str(x) for x in SurgeHeights] #make them strings if they were ints
        selection = [exp for exp in selection if exp.SurgeLevel.corresponding_SurgeHeight.name in SurgeHeights]
    
    if not Mayors == 'All':
        if not isinstance(Mayors,list):
            Mayors = [Mayors]
        selection = [exp for exp in selection if exp.name.split('_')[-1] in Mayors]
    
    return selection
    
        
class Model():
    def __init__(self,name):
        self.name = name
        self.allFloodProtection = [] #List with all the flood protection objects relevant for the city
        self.allResidentialArea = [] #list with all the residential areas in the city
        self.Parameters = {} #Dict containing all model parameters <TODO: Why should you do this with a dict; can be objects also!>
        
    def add_FloodProtection(self,FloodProtection): #Add flood protection object to model
        self.allFloodProtection.append(FloodProtection)
    
    def add_ResidentialArea(self,ResidentialArea): #Add residential area to model
        self.allResidentialArea.append(ResidentialArea)
        
    #def add_Measure_FloodProtection(self,Measure_FloodProtection):
    #    self.allMeasures.append(Measure_FloodProtection)
        
    #def add_Measure_ResidentialArea(self,Measure_ResidentialArea):
    #    self.allMeasures.append(Measure_ResidentialArea)
        
    def add_Parameter(self,parameter_name,parameter_value): #Add parameter to the dict containing all parameters
        self.Parameters[parameter_name] = parameter_value
    
    def __repr__(self):
        name = self.name
        FP_string = "allFloodProtection: \n" + "".join(str(x.name) + " " + str(x.baseline_level) + "; " for x in self.allFloodProtection)
        RA_string = "allResidentialArea: \n" + "".join((str(x.name) + " Protected by:" + str(x.protected_by) + "\n") for x in self.allResidentialArea)
        par_string = "Parameters : \n" + str(self.Parameters)
        return "{} \n-----------\n{} \n-----------\n{}\n{}".format(name,FP_string,RA_string,par_string)
    
    def __str__(self):
        return "Model: {} \nFloodProtection objects: {} \nResidentialAreas: {}".format(
            self.name, 
            "".join(str(x.name) + "; " for x in self.allFloodProtection), 
            "".join(str(x.name) + "; " for x in self.allResidentialArea))
        
class Mayor(ABC): #is subclass of ABC (abstract base class)
    @abstractmethod #in te vullen door subclasses (verplicht!)
    def apply_strategy(self,Model,SurgeSeries,Measures,i,time):
        pass
    
    @abstractmethod
    def get_name(self):
        pass
    
    def __str__(self): #this is what you see if you say "print(object)" #readable
        return self.get_name()


class SLR_Scenario:
    """
    A SLR_Scenario is a timeseries indicating the degree of
    sea level rise for each timestep.
    
    #TODO: add that it remembers the RCP?
    """
    def __init__(self,name,years=None,sealevel=None,description=None):
        allSLR_Scenario.append(self)
        self.name = name
        self.years = years
        self.sealevel = sealevel
        self.description = description

    def from_csv(self,filepath):
        """Add data from SLR trendseries from a csv file
        First column should contain the years
        Second column the water levels [m]
        """ 
        years = []
        sealevel = []
        
        with open(filepath) as f:
            reader = csv.reader(f)
            for row in reader:
                years.append(row[0])
                sealevel.append(row[1])

        self.years = [int(i) for i in years]
        self.sealevel = [float(i) for i in sealevel] #convert strings to floats
        
    def plot(self):
        df = pd.DataFrame(self.sealevel,index=self.years)
        return df.plot()
    
    def to_pickle(self,folder,filename=None):
        """
        Save SLR_Scenario object as a pickle
        
        Arguments:
            *self* (SLR_Scenario) : The SLR_Scenario object
            *folder* (string) : Path to destination folder
            *filename* (string) : Filename (optional, defaults to self.name.pkl)
        """
        if filename == None:
            filename = self.name + ".pkl"
        
        with open(os.path.join(folder,filename),'wb') as f:
            pickle.dump(self,f)
        
        
        
    
    def __repr__(self):
        return self.name +  "\n" + str(list(zip(self.years,self.sealevel)))
    
    def __str__(self):
        return self.name
    
def SLR_Scenario_from_pickles(folder,empty=True):
    """
    Load all SLR_Scenario pickles from a certain folder,
    while emptying any existing scenarios already added to the folder (optional)
    """
    
    if empty:
        allSLR_Scenario = []
    
    for filename in os.listdir(folder):
        if filename.endswith(".pkl"):
            with open(os.path.join(folder,filename),'rb') as f:
                allSLR_Scenario.append(pickle.load(f))
    return allSLR_Scenario #TODO HERE SOMETHING GOES WRONG WITH GLOBALS 
    
class SurgeHeight:
    """
    A SurgeHeight is a timeseries indicating the storm surge height
    irrespective of the sea level.
    
    This should be added to the sea level to get the storm surge level
    
    """
    def __init__(self,name):
        allSurgeHeight.append(self)
        self.name = name   

    def from_csv(self,filepath):
        """Get the Surge Height from a transient surge scenario
        """ 
        years = []
        surgelevel = []
        
        with open(filepath) as f:
            reader = csv.reader(f)
            for row in reader:
                years.append(row[0])
                surgelevel.append(row[1])

        self.years = [int(i) for i in years]
        self.surgeheight = [float(i) for i in surgelevel] #convert strings to floats

    def __repr__(self):
        return self.name +  "\n" + str(list(zip(self.years,self.surgeheight)))
    
    def __str__(self):
        return self.name
    
class SurgeLevel:
    """
    A SurgeLevel is a timeseries indicating the storm surge level per year,
    which is the sum of sea level rise + surge height in that year.
    
    """ 
    def __init__(self,name=None):
        self.name = name
        allSurgeLevel.append(self) #Add to the overview of all flood protection objects
    
    def from_combination(self,SLR_Scenario,SurgeHeight):
        """
        Fill the years and surge levels by combining a SLR Scenario object and
        a SurgeHeight object
        Will only calculate the sum for years for which data is available in both input timeseries
        
        """
        self.corresponding_SLR_Scenario = SLR_Scenario
        self.corresponding_SurgeHeight = SurgeHeight
        
        startvalue = max(min(SLR_Scenario.years),min(SurgeHeight.years))
        endvalue = min(max(SLR_Scenario.years),max(SurgeHeight.years))
        self.years = list(range(startvalue,endvalue+1)) 
        sl = SLR_Scenario.sealevel[SLR_Scenario.years.index(startvalue):SLR_Scenario.years.index(endvalue)+1] #slice the correct sea levels
        sh = SurgeHeight.surgeheight[SurgeHeight.years.index(startvalue):SurgeHeight.years.index(endvalue)+1] #slice the correct sea levels
        self.surgelevel = [sum(x) for x in zip(sl,sh)] #element-wise sum

    def __repr__(self): #this is wat you see if you say "object" (without printing) meant to be detailed
        return self.name
        
    def __str__(self): #this is what you see if you say "print(object)" meant to be simple
        return self.name
    
    
def combine_SurgeLevel(SLR_Scenario,SurgeHeight):
    name = SLR_Scenario.name + "__" + SurgeHeight.name
    instance = SurgeLevel(name=name) #Create new instance of object
    instance.from_combination(SLR_Scenario,SurgeHeight) #derive data from combining both sources
    return instance

def generate_SurgeLevel_new(SLR,transient):
    """
    Generate a Sugelevel timeseries (=SLR + SurgeHeight)
    
    Arguments:
        *SLR* (string) : 'Transient' sea level rise scenario e.g. '01'
        *transient* (int) : Transient storm surge series
    
    Returns:
        *SurgeLevel* (SurgeLevel object) : has time, surgelevel per time and some metadata
    """
    #load all SLR scenarios available as pickles
    allSLR_Scenario = SLR_Scenario_from_pickles(os.path.join("SLR_projections","Transients"))
    #and select the right one
    SLR_obj = [x for x in allSLR_Scenario if x.name.split('__')[0].split('_')[1] == SLR][0]

    #READ THE TRANSIENT SURGEHEIGHT SCENARIO
    SH_folder = "SurgeHeight" ###TODO READ FROM CONFIG
    SH_name = str(transient)
    SH_path = os.path.join(SH_folder,SH_name+'.csv')
    
    if not os.path.exists(SH_path):
        print("SH path : {} does NOT EXIST".format(SH_path)) #throw an error!
        return None
    
    SH_obj = SurgeHeight(SH_name)
    SH_obj.from_csv(SH_path)
    
    SurgeLevel = combine_SurgeLevel(SLR_obj,SH_obj)    
    
    return SurgeLevel
    
    
def generate_SurgeLevel_transient(RCP,collapse,PDF,transient): #DEPRECIATED
    """
    Generate a SurgeLevel timeseries (=SLR + SurgeHeight)
    
    Arguments:
        *RCP* (string) : Representative Concentration Pathway e.g. 'RCP26'
        *collapse* (boolean) : Account for collapse of icesheets (i.e. use Bamber)
        *PDF* (int) : Percentage indicating the likelihood from the probability density function (e.g. 17)
        *transient* (int) : Integer indicating which transient scenario to use
        
    Returns:
        *SurgeLevel* (SurgeLevel object) : has time, surgelevel per time and some metadata
    """
    if collapse: 
        SLR_source = "Bamber_2019"
        RCP = "high" #this is weird, but works for now
    else:
        SLR_source = "SROCC_2019" 
    
    #READ THE SLR INFO
    SLR_folder = "SLR_projections" ###TODO CHANGE WITH CONFIG
    SLR_name = "{}_{}_{}".format(SLR_source,RCP,PDF)
    SLR_path = os.path.join(SLR_folder,SLR_name+'.csv')
    
    if not os.path.exists(SLR_path):
        print("SLR path : {} does NOT EXIST".format(SLR_path)) #throw an error!
        return None
    
    SLR_obj = SLR_Scenario(SLR_name) #Create instance of object
    SLR_obj.from_csv(SLR_path)
    
    #READ THE TRANSIENT SCENARIO
    SH_folder = "SurgeHeight" ###TODO READ FROM CONFIG
    SH_name = str(transient)
    SH_path = os.path.join(SH_folder,SH_name+'.csv')
    
    if not os.path.exists(SH_path):
        print("SH path : {} does NOT EXIST".format(SH_path)) #throw an error!
        return None
    
    SH_obj = SurgeHeight(SH_name)
    SH_obj.from_csv(SH_path)
    
    SurgeLevel = combine_SurgeLevel(SLR_obj,SH_obj)

    return SurgeLevel

class FloodProtection:
    """
    Initiate FloodProtection class, which are flood protection infrastructures which...
     - Protect a certain area
     - Against flood with a certain water level (in the baseline situation)
     - Moveable barrier?
    """
    
    def __init__(self,name,baseline_level,moveable,description=None):
        self.name = name #Name of the flood protection object (string)
        self.baseline_level = baseline_level #initial level of flood protection
        self.protection_level = baseline_level #is something that changes of time
        self.barrier = moveable
        self.description = description
        self.activeMeasure = [] #initially, there are no active measures for the FP object
        
    def init_time(self,time): #If the model is run over time, initialise lists to store the results for the variables of interest
        self.protection_level = [self.baseline_level] * len(time) #store the development of flood protection over time
        self.measure_history = [0] * len(time) #store in which timestep which measures were taken
        
    def reset_protection_level(self):
        "Reset the flood protection level to the level when it was initiated"
        self.protection_level = self.baseline_level
            
    def __repr__(self):
        return self.name + str(self.baseline_level) + str(self.protection_level) + str(self.barrier) + self.description
    
    def __str__(self): #this is what you see if you say "print(object)"
        return self.name + str(self.protection_level)

class ResidentialArea():
    #trust_0 = 70 #initial trust of citizens, same for all residential areas
    
    def __init__(self,name,elevation,surface_area,inhabitants,nr_houses,house_price_0,dam_pars,dam_pars_household,protected_by,description=None):
        self.name = name #Name of the object (string)
        self.elevation = elevation #Elevation of the Residential Area in m
        self.surface_area = surface_area #Surface area in km2
        self.inhabitants = inhabitants #nr of inhabitants
        self.nr_houses = nr_houses #nr of houses
        self.house_price_0 = house_price_0 #price of a house at t0
        self.house_price_horizon = 80 #assume a time-horizon for house-time of 80 years
        self.r = 0.03 #discount factor (per year)
        self.dam_pars = dam_pars #Parameters for the depth-damage calculation in the area
        self.dam_pars_household = dam_pars_household #Parameter for the detph-damage calculation per household
        self.protected_by = protected_by #Names of the FloodProtection objects it is protected by
        self.description = description
    
    def init_time(self,time,trust_0=70,risk_perception_0=0): #If the model is run over time, initialise lists to store the results for the variables of interest
        self.trust_t = [float("NaN")] * len(time)
        self.trust_t[0] = trust_0 #set initial condition
        self.event_impact_history = [0] * len(time) #TO SAVE VALUES OF THE 'ALARMING CONDITIONS'
        self.event_history = [""] * len(time) #NEW, BECAUSE THE REST WILL BE DISCARDED!
        self.flood_history = [float("NaN")] * len(time) #SAVE THE INUNDATION DEPTHS
        self.nearmiss_history = [float("NaN")] * len(time) #SAVE THE DIFFERENCE BETWEEN THE DIKE HEIGHT AND PROTECTION LEVEL IN CASE OF NEAR MISS [0, 0.5]
        self.flood_damage = [float("NaN")] * len(time) #SAVE THE FLOOD DAMAGE
        self.risk = [float("NaN")] * len(time) #to save the objective risk per RA
        self.risk_household = [float("NaN")] * len(time) #risk per household
        self.risk_household_perceived = [float("NaN")] * len(time) #risk per household
        self.risk_household_discounted = [float("NaN")] * len(time) #discounted risk per household
        self.risk_household_discounted_perceived = [float("NaN")] * len(time) #discounted risk per household
        self.protection_level_rp = [float("NaN")] * len(time) #save the protection level of the return period #TODO: BETTER TO DO THIS AT THE LEVEL OF THE FLOOD PROTECTION OBJECT
        self.risk_perception = [float("NaN")] * len(time) #Fluctuating risk perception indicator
        self.risk_perception[0] = risk_perception_0
        #Varies between 0 and 1, with 0.5 indicating that perceptions equals objective risk
        self.risk_perceived = [float("NaN")] * len(time) #to save the subjective/perceived risk
        self.house_price_t_subjective = [float("NaN")] * len(time) #To save the development of house prices over time
        self.house_price_t_objective = [float("NaN")] * len(time) #To save the development of house prices over time
        self.house_price_t_subjective[0] = self.house_price_0 # Set the first timestep
        self.house_price_t_objective[0] = self.house_price_0 # Set the first timestep
        
        #Implemented on 20 August:
        self.flood_proofing = [False] * len(time) #Boolean indicating if flood proofing was implemented
        
    def match_with_FloodProtection(self,allFloodProtection): #TODO Make sure that it does not add it two times!
        for i in allFloodProtection: #Iterate over all possible FloodProtections 
            for j in self.protected_by: #Iterate over the structures the area is protected by (for now only one! -> later expand and make decision rules if multiple exist)
                if i.name == j:
                    self.protection_level = i.protection_level
        
    def residential_capital(self):
        print(self.name + ": \u20ac" + str(self.nr_houses*self.house_price_0) + " _____ " + str(round(self.nr_houses*self.house_price_0*10**(-6))) + "mln \u20ac" )
  
    def calculate_damage(self,inundation,timestep=0):
        """
        Calculate flood damage for a residential area

        Input:
            *self.dam_pars* (tuple) : (MaxDamage_Residential,depth,dam_frac) describing damage functions
                                  euro/m2            m      (-)
            *inundation* (float) : Inundation depth in m
            *surface_area* (float) : Surface area of the region in km2
            *timestep* (int) : (optionally) model timestep to check if flood proofing was implemented

        Returns:
            *damage* (float) : damage to the area in 2010-Euros
            
            #TODO: OPLETTEN, JE ROEPT DEZE FUNCTIE OOK NOG EEN KEER AAN BIJ DE RISICO-BEREKENING!!
            #TODO: UPDATE THE DOCSTRING, USES ATTRIBUTE FROM .SELF RATHER THAN INPUT 
        """
              
        dam_fraction = np.interp(inundation,self.dam_pars[1],self.dam_pars[2]) #fraction of max damage
        max_damage = self.dam_pars[0]
        damage = int(round(max_damage * 10**6 * self.surface_area * dam_fraction))
        
        #TO GUARANTEE BACKWARD COMPATABILITY, CHECK IF THE FLOOD PROOFING WAS IMPLEMENTED AT ALL
        if hasattr(self,'flood_proofing'):
            if self.flood_proofing[timestep]: #if True, the flood_proofing is implemented in this timestep
                #Carry out the flood proofing procedure of Haer et al., (2017)
                if inundation < 1: #flood proofing only works if water depth < 1 m
                    #print('Flood proofing active in timestep {}'.format(timestep))
                    damage = damage * 0.3 #70% reduction of damage
                
        return damage
    
    def calculate_damage_household(self,inundation,timestep=0):
        """
        Calculate flood damage for one household in the residential area
        
        Input:
            *inundation* (float) : Inundation depth in m
            *timestep* (int) : (optionally) model timestep to check if flood proofing was implemented

        Returns:
            *damage* (float) : damage to a household in 2010-Euros
            
            #TODO: OPLETTEN, JE ROEPT DEZE FUNCTIE OOK NOG EEN KEER AAN BIJ DE RISICO-BEREKENING!!!
        """
        dam_fraction = np.interp(inundation,self.dam_pars_household[1],self.dam_pars_household[2]) #fraction of max damage
        max_damage = self.dam_pars_household[0]
        damage = int(round(max_damage*dam_fraction))
        
        #TO GUARANTEE BACKWARD COMPATABILITY, CHECK IF THE FLOOD PROOFING WAS IMPLEMENTED AT ALL
        if hasattr(self,'flood_proofing'):
            if self.flood_proofing[timestep]: #if True, the flood_proofing is implemented in this timestep
                #Carry out the flood proofing procedure of Haer et al., (2017)
                if inundation < 1: #flood proofing only works if water depth < 1 m
                    #print('Flood proofing active in timestep {}'.format(timestep))
                    damage = damage * 0.3 #70% reduction of damage  
        return damage
      
        
    def weigh_RP_Bayesian(self,time,I_exp_interp,I_social):
        """"
        Apply Bayesian learning to the Risk Perception
        This varies between 0 () and 1
        Adapted from Haer et al. (2017) citing Viscusi (1985,1989)
        
        Input:
            *time* (int) : timestep of the model
            *I_exp_max* (float) : Water depth at which the maximum experience occurs [currently unused but hardcoded]
            *I_social* (float) : Impact of neighbouring residential areas through media
            
        Returns:
            *self.risk_perception(time)* (float) : The risk perception in the current timestep
        """        
        
        depth = self.flood_history[time]  #water depth
        nearmiss = self.nearmiss_history[time]
        
        #set_trace()
        
        if depth > 0: #IN CASE OF A FLOOD
            #print('timestep: {}, region: {}, FLOOD!'.format(time,self.name))
            a = self.Bayesian_pars.a[2] 
            b = self.Bayesian_pars.b[2] 
            c = self.Bayesian_pars.c[2] 
            #unpack values to enable the linear interpolation
            #TODO: CHANGE THE I_exp_interp(...)
            #xp = I_exp_interp['xp'] 
            #fp = I_exp_interp['fp']
            #linear interpolation of I_exp
            I_exp = np.interp(depth,[0,0.5],[0,1],left=0,right=1)
            
        else: #IF NO FLOOD OCCURS
            if nearmiss > 0: #IN CASE OF A NEAR MISS
                #print('timestep: {}, region: {}, NEAR MISS!'.format(time,self.name))
                a = self.Bayesian_pars.a[1] #Select the first weighting factor ...
                b = self.Bayesian_pars.b[1] #... from the list of weighting factors ...
                c = self.Bayesian_pars.c[1] #... (see docstring of Bayesian_pars class)
                I_exp = np.interp(nearmiss,[0,0.5],[1,0],left=1,right=0)
            else: #IN CASE OF A NO FLOOD NOR A NEAR MISS
                #print('timestep: {}, region {}, NOTHING'.format(time,self.name))
                a = self.Bayesian_pars.a[0] #Select the first weighting factor ...
                b = self.Bayesian_pars.b[0] #... from the list of weighting factors ...
                c = self.Bayesian_pars.c[0] #... (see docstring of Bayesian_pars class)
                I_exp = 0 #does not impact the calculation, but needs to be defined #TODO NO HARDCODING      
        #set_trace()   
        #Function should not be applied in the first timestep t=0, use initial condition instead in this timestep
        self.risk_perception[time] = (
        a * self.risk_perception[time-1] + b * I_exp + c * I_social) / (
        a + b + c)  
        
    def __repr__(self): #this is wat you see if you say "object" (without printing)
        return self.name + " Elevation: " + str(self.elevation) + "\n Protected by: " + str(self.protected_by)
        
    def __str__(self): #this is what you see if you say "print(object)" #readable
        return self.__dict__

def discount_risk(EAD,discount=0.03,horizon=80):
    """
    Calculated discounted flood risk for a time series of expected annual damage
    
    Arguments:
        *EAD* (list of floats) : the EAD to discount over
        *r* (float) : discount factor per year
        *horizon* (int) : time horizon to discount over
        
    Returns:
        *Risk_discounted* (float) : discounted risk in t=0
    
    """
    if horizon > len(EAD): #the requested horizon is longer than the available EADs
        raise ValueError("The requested time horizon {} is longer than amount of available EADs {}".format(horizon,len(EAD)))
    
    selected_EAD = EAD[0:horizon]
    timesteps = list(range(0,horizon))
    df_t = [1 / (1+discount)**t for t in timesteps] #calculate discount factor per timestep
    npvs = [None] * len(timesteps)
    for t in range(len(timesteps)):
        npvs[t] = EAD[t] * df_t[t]
    
    return sum(npvs)


class Bayesian_pars():
    """
    Class for objects containing the parameters for Bayesian weighting.

    Expects to use the following equation for Bayesian weighting: (Haer et al., 2017)
    
                 [a*RP_t + b*I_experience + c*I_media/neighbours ] 
    RP_t+1 =    --------------------------------------------------------
                                  [a + b + c]
    
    Convention for arguments a-c
    if list of length 1: this weighting factor always applies
    if list of length 2: list[0] = no flood; list[1] = flood
    if list of length 3: list[0] = no flood; list[1] = near miss; list[2] = flood
    
    Arguments:
        *a* (list of floats) : weighting factor for risk perception in the previous timestep
        *b* (list of floats) : weighting factor for flood experience in the current timestep
        *c* (list of floats) : weighting factor for impact of the media/science/other external influence (in our case from other regions)
    
    """
    def __init__(self,a,b,c):
        self.a = a
        self.b = b
        self.c = c
    
allactiveMeasure = []

def allactiveMeasure_reset():
    allactiveMeasure = []
    
class Measure():
    def __init__(self,name,lead_time):
        self.name = name
        self.lead_time = lead_time #time it takes to implement the measure
        
    def __repr__(self):
        return self.name + " " + str(self.lead_time) + " " + str(self.heightening)
        
    def plan_measure(self,apply_to,i):
        self.apply_to = apply_to #flood protection object to which measure should be applied
        #hier nu ergens gaan kijken wat voor maatregelen er precies zijn
        self.time_to_implementation = self.lead_time
        allactiveMeasure.append(self)
        #### houd ergens bij in de historie dat je deze measure gepland hebt.
        apply_to.measure_history[i] = self.heightening #can be made nicer
        
    def countdown(self,i,end):#counts down, and if counter = 0 implements the measure
        if self.time_to_implementation > 0:
            self.time_to_implementation = self.time_to_implementation - 1
        elif self.time_to_implementation == 0:
            self.implement_measure(i,end)
            #print(self,'implemented!')
        
class Measure_FloodProtection(Measure):
    def __init__(self,name,lead_time,heightening):
        super().__init__(name,lead_time)
        self.heightening = heightening
    
    def implement_measure(self,i,end):
        #print(self.apply_to.protection_level)
        #print(self.heightening)
        self.apply_to.protection_level[i:end] = [self.apply_to.protection_level[i] + self.heightening] * (end-i)
        #print(self.apply_to.protection_level)
        allactiveMeasure.remove(self) #remove the measure from the active measure list
        
class Measure_ResidentialArea(Measure):
    def __init__(self,name,lead_time,heightening):
        super().__init__(name,lead_time)
        self.heightening = heightening
    
def evaluate_event(water_level_difference,alarming_conditions,report):
    """Returns a decrease in trust for a given difference between flood protection and observed storm surge level
    Inputs:
     *water_level_difference* (float) -- Flood protection level - storm surge level (so positive if flood occurs)
     *alarming_conditions* (OrderedDict) -- Dict containing the possible event thresholds
     *report* (boolean) -- Reports what the function is doing
    
    Return: a decrease in trust
    """ 
    for key, value in alarming_conditions.items():
        #print (key, value)
        if water_level_difference >= key:
            if report:
                print("This is a: {}, so trust goes down with {}".format(value[0],value[1]))
            break
    trust = value[1]
    return trust

def Gumbel(x,mu,beta):
    "Returns the cumulative probability that X <= xp"
    return exp(-1* exp((mu-x)/beta))

def Gumbel_inverse(RP,mu,beta):
    "Returns the water level h (m) for a Gumbel distributed PDF"
    waterlevel = mu - beta * log(-1 * log((RP-1)/RP))
    return waterlevel

def Gumbel_RP(h,mu,beta):
    "Returns the Return Period (years) of the event with a certain storm surge height in m"
    return 1/(1-Gumbel(h,mu,beta))

def shift_subjective_floods(return_periods,risk_perception_factor):
    """
    Shifts an objective series of return periods of flood events to account for changes in risk perception
    Uses equation X from Haer et al., (2017)
    
    Arguments:
        *return_periods* (list of floats) - return periods flood events [years]
                         (float) - can also handle a single float
        *risk_perception_factor* (float) - risk perception indicator [0,1]
    
    Returns:
        *perceived_return_periods* (list of floats) - perceived return periods of flood events [years]
    
    The risk_perception_factor varies between 0 and 1 and is the ouput of the weigh_RP_Bayesian function
     -> 0 represents overconfidence
     -> 0.5 represents risk perception = actual risk
     -> 1 represents to much fear
    
    """
    RPs = return_periods
    RPf = risk_perception_factor
    
    if not 0 <= RPf <= 1:
        raise ValueError('Risk perception factor should be float between 0 and 1, not {}'.format(RPf))
    
    
    ################ ONLY FOR PROPERLY HANDLING FLOATS AND INTEGERS #############
    convertback = False #by default don't convert list back to float
    if isinstance(RPs,(int,float)): #convert instances or floats to lift
        convertback = True #need to convert back when returning!
        RPs = [RPs] #add to list
    ################ END #############
    
    RPs_shifted = [None] * len(RPs)
    
    #Translate the value between 0 and 1 to a value between -10 to 10
    factor = 10**(2*RPf-1) #Botzen et al., 2009, Dutch Households
    
    for i, RP in enumerate(RPs):
        p = 1/RP #probability is the inverse of the return period
        pi = factor * p #perceived probability is obtained by multiplication by the factor
        RPs_shifted[i] = 1/pi #perceived return period it the inverse of the perceived probability
    
    ################ ONLY FOR PROPERLY HANDLING FLOATS AND INTEGERS #############
    if convertback:
        RPs_shifted = RPs_shifted[0]
    ################ END #############
    
    return RPs_shifted
        
        
    
    

#Taken from the OSdaMage model (vs 1.0) [Van Ginkel et al. 2020]
def risk_FP(dam,RPs,PL):
    """
    Calculates the flood risk from damage estimates and corresponding return periods by trapezoidal integration, 
    accounting for the flood protection in place. 
    
    Arguments:
        *dam* (list) - damage estimates (e.g. Euro's) - from high to low RPs
        *RPs* (list) - the return periods (in years) of the events corresponding to these damage estimates - from high to low RPs (order of both lists should match!) 
        *PL* (integer) - the flood protection level in years
    
    Returns:
        *risk* (float) - the estimated flood risk in Euro/y
    
    Note that this calculation is not trivial and contains important assumptions about the risk calculation:
     - Damage for RPs higher than the largest RP equals the damage of the largest RP
     - Damage for RPs lower than the smallest RP is 0.
     - Damage of events in between known RPs are interpolated linearly with RP.
    """
    if not sorted(RPs, reverse=True) == RPs:
        raise ValueError('RPs is not provided in the right format. Should be a descending list of RPs, e.g. [500,100,10]')
    
    if RPs[-1] < PL < RPs[0]: #if protection level is somewhere between the minimum and maximum available return period
        pos = RPs.index(next(i for i in RPs if i < PL)) #find position of first RP value < PL; this is the point which need to be altered
        dam = dam[0:pos+1] #remove all the values with smaller RPs than the PL
        dam[pos] = np.interp(x=(1/PL),xp=[(1/RPs[pos-1]),(1/RPs[pos])],fp=[dam[pos-1],dam[pos]]) #interpolate the damage at the RP of the PL
        #note that you should interpolate over the probabilities/frequences (therefore the 1/X), not over the RPs; this gives different results
        RPs[pos] = PL #take the PL as the last RP...
        RPs = RPs[0:pos+1] #... and remove all the other RPs

    elif PL >= RPs[0]: #protection level is larger than the largest simulated event
        return (1/PL) * dam[0] #damage is return frequence of PL times the damage of the most extreme event

    #not necessary to check other condition (PL <= 10 year -> then just integrate over the available damages, don't assume additional damage)
     
    dam.insert(0,dam[0]) #add the maximum damage to the list again (for the 1:inf event)
    Rfs = [1 / RP for RP in RPs] #calculate the return frequencies (probabilities) of the damage estimates
    Rfs.insert(0,0) #add the probability of the 1:inf event
    integral = np.trapz(y=dam,x=Rfs).round(2)
    return integral

class Metric():
    """
    Indicates which model outcome parameters should be considered model metrics
    """
    
    def __init__(self,index,data,name=None):
        """The raw indicator data, describes the development of the metric over time"""
        series = pd.Series(name=name,data=data,index=index)
        df = series.to_frame() #function below only works for dfs #TODO: is possibly also possible with series
        df[df<0] = 0 #Dirty work-around: avoid values below zero TODO.
        series = df.squeeze()
        self.raw = series
        self.name = name
    
    def __repr__(self):
        return "{}".format(self.name)
    
    def create_statistics(self,window=5,lag=1,domain='All'):
        """
        Create statistics for Panda Series, used for tipping point analysis
        Rolling window: result is set to the right edge of the window
        if Cut = true: don't show rows containing al NaNs
        
        Arguments:
            *self.statistics* (Dataframe) : columns are series with an output metric of interest
            *window* (int) : Width of the rolling window (in model timesteps)
            *lag* : unused
            *domain* (tuple) : tuple indicating the beginning and end year to include in the statistic
            
        Returns:
            *self.Statistics* (DataFrame) : 
        """
        #Construct empty df to store results
        series = self.raw
        df = pd.DataFrame(index=series.index,data=series)
        
        #Calculate derivates of raw time series
        df["{}".format("First order derivative (dM/dt)")] = series.to_frame().diff()
        df["{}".format("Second order derivative (d2M/dt2)")] = series.to_frame().diff().diff()
            #df["{} __ {}".format(series.name,"Autocorrelation lag {}".format(lag))] = series.autocorr(lag=lag)

        #Calculate statistics using a rolling window
        rolling = series.rolling(window=window)
        df["{}".format("Window mean")] = rolling.mean()
        df["{}".format("Window variance")] = rolling.var()
            #df["{} __ {}".format(series.name,"Window rolling correlation")] = rolling.apply(lambda x: x.autocorr(), raw=False)

        if not domain == 'All':
            df = df.loc[domain[0]:domain[1]]
        
        self.statistics = df
        return df
    
    
    def plot_statistics(self,figsize=(20,10),drop=None,save=False):
        statistics = self.statistics
        statisctics = statistics.drop(drop,axis=1)
        fig,ax = plt.subplots(nrows=len(statistics.columns),ncols=1,figsize=figsize,sharex=True)
        for i, col in enumerate(list(statistics.columns)):
            statistics[col].plot(ax=ax[i],title=col)
        fig.suptitle('{}'.format(statistics.columns[0]))
        if save:
            fig.savefig(os.path.join(output_path,"{}_{}_statistics.png".format("exp_name",statistics.columns[0],dpi=150)))
    
    def select_candidates(self,c1=0.15,c2=0.2e10,c3=10,window=5,margin=2):
        """
        Select tipping point candidates based on three criteria

        Arguments:
            *self.statistics* (DataFrame) : output of examine_series
            *c1* (float) : absolute change of house price as fraction of house price at t0: detect rapid change
            *c2* (float) : absolute valued threshold for variance: detect stable states
            *c3* (float) : percentage of change between states: substantially different states
            *window* (int) : window size for functionality using a moving window
            *margin* (int) : margin around TP for assessing stable states

        Returns:
            *df* (DataFrame) : indicating in which years the criteria are met

        """
        statistics = self.statistics
        ind = statistics.index
        df = pd.DataFrame(index=ind)

        #Criterion 1: check for rapid change
        #c1 = 5 #percentage of change per timestep (compared to house price at t0) considered rapid
        house_price_t0 = self.raw.iloc[0]
        #negative change
        df["rapid change_neg"] = pd.Series(index=ind,data=[-1]*len(ind)) \
                     [(statistics["First order derivative (dM/dt)"] <= -c1* house_price_t0)]
        #positive change
        df["rapid change_pos"] = pd.Series(index=ind,data=[1]*len(ind)) \
                     [(statistics["First order derivative (dM/dt)"] >= +c1* house_price_t0)]
        c1met = list(df[df["rapid change_neg"].notnull()].index) #list of years in which c1 is met
        c1met.append(list(df[df["rapid change_pos"].notnull()].index)) 
        
        
        #Criterion 2: check if variance is above threshold to detect stable states
        #c2 = 0.2e10 #absolute value of variance
        df["stable"] = pd.Series(index=ind,data=[2]*len(ind))[statistics["Window variance"] < c2]
        df["stable_before"] = pd.Series(index=ind,data=[1.8]*len(ind))[statistics["Window variance"].shift(periods=margin) < c2] #
        df["stable_after"] = pd.Series(index=ind,data=[2.2]*len(ind))[statistics["Window variance"].shift(periods=-margin-window) < c2] #
        

        #Criterion 3: check if states on both sides of threshold are different
        #c3 = 10 #percentage of change that states before and after should be different
        #c3met = []
        #for y in c1met:
        #    avg_b,avg_a = average_before_after(statistics.iloc[:,0],y,window=window,margin=margin)
        #    perc = 100*(avg_a-avg_b)/avg_a
        #    if (perc < -1*c3) or (perc > c3) :
        #        c3met.append(y)
        #df["substantial different states"] = pd.Series(index=c3met,data=[3]*len(c3met))
        self.candidates = df
    
        return df
    
    def plot_both(self,figsize=(15,20),save=False,output_path=None,drop=None,exp_name=None):
        """
        Plot metric statistics and candidate tipping points
        """
        statistics = self.statistics
        statistics = statistics.drop(drop,axis=1)
        candidates = self.candidates
        nrows = len(statistics.columns)+1
        fig,ax = plt.subplots(nrows=nrows,ncols=1,figsize=figsize,sharex=True)
        for i, col in enumerate(list(statistics.columns)):
            statistics[col].plot(ax=ax[i],title=col)
        fig.suptitle('{}_{}'.format(exp_name,statistics.columns[0]))
        candidates.plot(ax=ax[nrows-1],title='SETP candidates by criterion',style='o')
        if save: fig.savefig(os.path.join(output_path, \
                "{}_{}_statistics.png".format(exp_name,statistics.columns[0]),dpi=150,bbox_inches='tight'))
        return fig,ax
        
        

def average_before_after(data,year,window=5,margin=2):
    before = data.loc[year-margin-window:year-margin].mean()
    after = data.loc[year+margin:year+margin+window].mean()
    return(before,after)