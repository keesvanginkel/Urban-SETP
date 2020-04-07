import csv
import numpy as np
import os
from abc import ABC, abstractmethod


#TRACK THE OBJECTS THAT WERE INITIATED
allMeasure = []
allSurgeSeries = []   
#allFloodProtection = [] #List with all the flood protection objects relevant for the city
#allResidentialArea = [] #List of all the residential areas in the city

class Model():
    def __init__(self,name):
        self.name = name
        self.allFloodProtection = [] #List with all the flood protection objects relevant for the city
        self.allResidentialArea = [] #list with all the residential areas in the city
        self.allMeasures = [] #list with all possible flood protection measures
        self.Parameters = {} #Dict containing all model parameters
        
    def add_FloodProtection(self,FloodProtection): #Add flood protection object to model
        self.allFloodProtection.append(FloodProtection)
    
    def add_ResidentialArea(self,ResidentialArea): #Add residential area to model
        self.allResidentialArea.append(ResidentialArea)
        
    def add_Measure_FloodProtection(self,Measure_FloodProtection):
        self.allMeasures.append(Measure_FloodProtection)
        
    def add_Measure_ResidentialArea(self,Measure_ResidentialArea):
        self.allMeasures.append(Measure_ResidentialArea)
        
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
    def apply_strategy(self,Model,SurgeSeries,i,time):
        pass
    
    @abstractmethod
    def get_name(self):
        pass
        

class SurgeSeries:
    "Common class for all storm surge series"
    def __init__(self,allSurgeSeries,name=None,description=None,surgelevel=None,years=np.arange(2021,2121)):
        self.name = name
        self.description = description
        self.surgelevel = surgelevel
        self.years = years
        allSurgeSeries.append(self) #Add to the overview of all flood protection objects
        
    def to_csv(self,filename):
        "Write to a csv file (weakness: does not save the metadata yet)"
        zipped = list(zip(self.years,self.surgelevel)) #zip the two lists
        with open(os.path.join("SurgeSeries",filename), "w",newline='') as f:
            writer = csv.writer(f)
            for row in zipped:
                writer.writerow(row)
    
    def from_csv(self,filename):
        filename = os.path.join("SurgeSeries",filename)
        years = []
        surgelevel = []
        with open(filename) as f:
            reader = csv.reader(f)
            for row in reader:
                years.append(row[0])
                surgelevel.append(row[1])
        self.years = [int(i) for i in years]
        self.surgelevel = [float(i) for i in surgelevel] #convert strings to floats
        
    def __repr__(self): #this is wat you see if you say "object" (without printing) meant to be detailed
        return self.name + " " + self.description + "\n" + str(list(zip(self.years,self.surgelevel)))
        
    def __str__(self): #this is what you see if you say "print(object)" meant to be simple
        return self.name + " " + self.description + "\n" +  str(list(zip(self.years,self.surgelevel)))



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
        self.protection_level = baseline_level #initial level of flood protection
        self.barrier = moveable
        self.description = description
        self.underconstruction = 0
        
    def update_protection_level(self,start,end,newvalue,lead_time):
        "Update the flood protection level  from start to end timestep with a new value"
        self.protection_level[start:end] = [newvalue] * (end-start)
        
        "Indicate that the Flood Protection object is currently under construction for n years"
        self.underconstruction = lead_time
         
    def reset_protection_level(self):
        "Reset the flood protection level to the level when it was initiated"
        self.protection_level = self.baseline_level
        
    def construction_progress(self):
        "Withdraw from the construction time"
        if self.underconstruction > 0:
            self.underconstruction = self.underconstruction - 1
    
    def __repr__(self):
        return self.name + int(self.baseline_level) + self.protection_level + self.barrier + self.description
    
    def __str__(self): #this is what you see if you say "print(object)"
        return self.name + str(self.protection_level)

class ResidentialArea():
    #trust_0 = 70 #initial trust of citizens, same for all residential areas
    
    def __init__(self,name,elevation,surface_area,dam_pars,protected_by,description=None,trust_0=70):
        self.name = name #Name of the object (string)
        self.elevation = elevation #Elevation of the Residential Area in m
        self.surface_area = surface_area #Surface area in km2
        self.dam_pars = dam_pars #Parameters for the depth-damage calculation in the area
        self.protected_by = protected_by #Names of the FloodProtection objects it is protected by
        self.description = description
        self.trust_0 = trust_0
    
    def init_time(self,time): #If the model is run over time, initialise lists to store the results for the variables of interest
        self.trust_t = [None] * len(time)
        self.trust_t[0] = self.trust_0 #set initial condition
        self.event_impact_history = [0] * len(time) #TO SAVE VALUES OF THE 'ALARMING CONDITIONS'
        self.flood_history = [None] * len(time)
    
    def match_with_FloodProtection(self,allFloodProtection): #TODO Make sure that it does not add it two times!
        for i in allFloodProtection: #Iterate over all possible FloodProtections 
            for j in self.protected_by: #Iterate over the structures the area is protected by (for now only one! -> later expand and make decision rules if multiple exist)
                if i.name == j:
                    self.protection_level = i.protection_level
  
    def calculate_damage(self,inundation):
        """
        Calculate flood damage for a residential area

        Input:
            *self.dam_pars* (tuple) : (MaxDamage_Residential,depth,dam_frac) describing damage functions
                                  euro/m2            m      (-)
            *inundation* (float) : Inundation depth in m
            *surface_area* (float) : Surface area of the region in km2

        Returns:
            *damage* (float) : damage to the area in 2010-Euros
        """
        dam_fraction = np.interp(inundation,self.dam_pars[1],self.dam_pars[2]) #fraction of max damage
        max_damage = self.dam_pars[0]
        return int(round(max_damage * 10**6 * self.surface_area * dam_fraction))
                    
    def __repr__(self): #this is wat you see if you say "object" (without printing)
        return self.name + " Elevation: " + str(self.elevation) + "\n Protected by: " + str(self.protected_by)
        
    def __str__(self): #this is what you see if you say "print(object)" #readable
        return self.__dict__


class Measure():
    def __init__(self,name,lead_time):
        self.name = name
        self.lead_time = lead_time
        
    def __repr__(self):
        return self.name + " " + str(self.lead_time) + " " + str(self.heightening)
        
class Measure_FloodProtection(Measure):
    def __init__(self,name,lead_time,heightening):
        super().__init__(name,lead_time)
        self.heightening = heightening
        
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