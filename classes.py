import csv
import numpy as np
import os

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
        
    def __repr__(self): #this is wat you see if you say "object" (without printing)
        return self.name + " " + self.description + "\n" + str(list(zip(self.years,self.surgelevel)))
        
    def __str__(self): #this is what you see if you say "print(object)"
        return self.name + " " + self.description + "\n" +  str(list(zip(self.years,self.surgelevel)))
    
allFloodProtection = [] #List with all the flood protection objects relevant for the city
allResidentialArea = [] #List of all the residential areas in the city

class FloodProtection:
    """
    Initiate FloodProtection class, which are flood protection infrastructures which...
     - Protect a certain area
     - Against flood with a certain water level (in the baseline situation)
     - Moveable barrier?
    """
    
    def __init__(self,name,baseline_level,moveable):
        self.name = name #Name of the flood protection object (string)
        self.baseline_level = baseline_level #initial level of flood protection
        self.protection_level = baseline_level #initial level of flood protection
        self.barrier = moveable
        allFloodProtection.append(self) #Add to the overview of all flood protection objects
        
    #def update_protection_level(self,increase):
    #    """Update a flood protection level object with some meters"""
    #    self.protection_level = self.protection_level + increase
        
    def update_protection_level(self,SurgeSeries,start,end,newvalue):
        "Update the flood protection level for a certain SurgeSeries (experiment) from start to end timestep with a new value"
        self.protection_level[SurgeSeries][start:end] = [newvalue] * (end-start)
        
        
    def reset_protection_level(self):
        "Reset the flood protection level to the level when it was initiated"
        self.protection_level = self.baseline_level
    
    def __str__(self): #this is what you see if you say "print(object)"
        return self.name + str(self.protection_level)

class ResidentialArea():
    trust_0 = 70 #initial trust of citizens, same for all residential areas
    
    def __init__(self,name,elevation,protected_by):
        self.name = name #Name of the object (string)
        self.elevation = elevation #Elevation of the Residential Area in m
        self.protected_by = protected_by #Names of the FloodProtection objects it is protected by
        
        allResidentialArea.append(self) #Add to the overview of all flood protection objects
    
    def match_with_FloodProtection(self): #TODO Make sure that it does not add it two times!
        for i in allFloodProtection: #Iterate over all possible FloodProtections 
            for j in self.protected_by: #Iterate over the structures the area is protected by (for now only one! -> later expand and make decision rules if multiple exist)
                if i.name == j:
                    self.protection_level = i.protection_level
                    
    def __repr__(self): #this is wat you see if you say "object" (without printing)
        return self.name + " Elevation: " + str(self.elevation) + "\n Protected by: " + str(self.protected_by)
        
    def __str__(self): #this is what you see if you say "print(object)" #readable
        return self.__dict__

class Major:
    def __init__(self,name):
        self.name = name

allMeasure = []
class Measure():
    def __init__(self,name,increase,lead_time):
        self.name = name
        self.increase = increase #the increase in height of the flood protection measure in m
        self.lead_time = lead_time
        
        allMeasure.append(self)
    
    
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