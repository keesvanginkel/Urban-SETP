import csv
import numpy as np
import os
from abc import ABC, abstractmethod
from math import log, exp


#TRACK THE OBJECTS THAT WERE INITIATED
allSurgeSeries = []   

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
    def apply_strategy(self,Model,SurgeSeries,i,time):
        pass
    
    @abstractmethod
    def get_name(self):
        pass
    
    def __str__(self): #this is what you see if you say "print(object)" #readable
        return self.get_name()
        



allSLR_Scenario = []
allSurgeHeight = []
allSurgeLevel = []

class SLR_Scenario:
    """
    A SLR_Scenario is a timeseries indicating the degree of
    sea level rise for each timestep.
    
    #TODO: add that it remembers the RCP?
    """
    def __init__(self,name):
        allSLR_Scenario.append(self)
        self.name = name

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
        
    def __repr__(self):
        return self.name +  "\n" + str(list(zip(self.years,self.sealevel)))
    
    def __str__(self):
        return self.name
    
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
        
    #def to_csv(self,filename):
    #    "Write to a csv file (weakness: does not save the metadata yet)"
    #    zipped = list(zip(self.years,self.surgelevel)) #zip the two lists
    #    with open(os.path.join("SurgeSeries",filename), "w",newline='') as f:
    #        writer = csv.writer(f)
    #        for row in zipped:
    #            writer.writerow(row)
    
    #def from_csv(self,filename):
    #    filename = os.path.join("SurgeSeries",filename)
    #    years = []
    #    surgelevel = []
    #    with open(filename) as f:
    #        reader = csv.reader(f)
    #        for row in reader:
    #            years.append(row[0])
    #            surgelevel.append(row[1])
    #    self.years = [int(i) for i in years]
    #    self.surgelevel = [float(i) for i in surgelevel] #convert strings to floats
        


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
    
    def __init__(self,name,elevation,surface_area,inhabitants,nr_houses,house_price_0,dam_pars,protected_by,description=None):
        self.name = name #Name of the object (string)
        self.elevation = elevation #Elevation of the Residential Area in m
        self.surface_area = surface_area #Surface area in km2
        self.inhabitants = inhabitants #nr of inhabitants
        self.nr_houses = nr_houses #nr of houses
        self.house_price_0 = house_price_0 #price of a house at t0 
        self.dam_pars = dam_pars #Parameters for the depth-damage calculation in the area
        self.protected_by = protected_by #Names of the FloodProtection objects it is protected by
        self.description = description
    
    def init_time(self,time,trust_0=70,risk_perception_0=0): #If the model is run over time, initialise lists to store the results for the variables of interest
        self.trust_t = [float("NaN")] * len(time)
        self.trust_t[0] = trust_0 #set initial condition
        self.event_impact_history = [0] * len(time) #TO SAVE VALUES OF THE 'ALARMING CONDITIONS'
        self.flood_history = [float("NaN")] * len(time) #SAVE THE INUNDATION DEPTHS
        self.flood_damage = [float("NaN")] * len(time) #SAVE THE FLOOD DAMAGE
        self.risk = [float("NaN")] * len(time) #to save the objective risk
        self.protection_level_rp = [float("NaN")] * len(time) #save the protection level of the return period #TODO: BETTER TO DO THIS AT THE LEVEL OF THE FLOOD PROTECTION OBJECT
        self.risk_perception = [float("NaN")] * len(time) #Fluctuating risk perception indicator
        self.risk_perception[0] = risk_perception_0
        #Varies between 0 and 1, with 0.5 indicating that perceptions equals objective risk
        self.risk_perceived = [float("NaN")] * len(time) #to save the subjective/perceived risk
        
    def match_with_FloodProtection(self,allFloodProtection): #TODO Make sure that it does not add it two times!
        for i in allFloodProtection: #Iterate over all possible FloodProtections 
            for j in self.protected_by: #Iterate over the structures the area is protected by (for now only one! -> later expand and make decision rules if multiple exist)
                if i.name == j:
                    self.protection_level = i.protection_level
    
    def init_Bayesian(self,Bayesian_pars):
        """
        Add the weighting factors of the Bayesian weighting to to the residential area
        
        Arguments:
            *self* (ResidentialArea) : The residential area with all it's properties
            *Bayesian_pars* (Bayesian_pars) : Object containing Bayesian weighting parameters 
        """
        pass
    
    def residential_capital(self):
        print(self.name + ": \u20ac" + str(self.nr_houses*self.house_price_0) + " _____ " + str(round(self.nr_houses*self.house_price_0*10**(-6))) + "mln \u20ac" )
  
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
    
    def weigh_RP_Bayesian(self,time,Bayesian_pars,I_exp_interp,I_social=0,I_media=0.5):
        """"
        Apply Bayesian learning to the Risk Perception
        This varies between 0 () and 1
        Adapted from Haer et al. (2017) citing Viscusi (1985,1989)
        
        Input:
            *time* (int) : timestep of the model
            *Bayesian_pars* (dict) : Weighting factors a,b,c,d for the Bayesian updating
            *I_exp_max* (float) : Water depth at which the maximum experience occurs
            *I_social* (float) : Impact of neighbours (if any)
            *I_media* (float) : Impact of media (if any)
            
        Returns:
            *self.risk_perception(time)* (float) : The risk perception in the current timestep
        """
        #Unpack the Bayesian weighing pars assigned to the model
        if self.flood_history[time] > 0: #in case of a flood
            b = Bayesian_pars["b_flood"]
            a = Bayesian_pars["a_flood"] * b
            
            #Calculate the magnitude of the flood experience
            depth = self.flood_history[time]  #water depth
            
            #unpack values to enable the linear interpolation
            xp = I_exp_interp['xp']
            fp = I_exp_interp['fp']
            #linear interpolation of I_exp
            I_exp = np.interp(depth,xp,fp,left=0,right=1)
        
        else:
            a = Bayesian_pars["a_noflood"] #no flood
            b = Bayesian_pars["b_noflood"]
            I_exp = 0
        
        c = Bayesian_pars["c"]
        d = Bayesian_pars["d"]
           
        #Function should not be applied in the first timestep t=0, use initial condition instead in this timestep
        self.risk_perception[time] = (
        a * self.risk_perception[time-1] + b * I_exp + c * I_social + d * I_media) / (
        a + b + c + d)    
        
    def __repr__(self): #this is wat you see if you say "object" (without printing)
        return self.name + " Elevation: " + str(self.elevation) + "\n Protected by: " + str(self.protected_by)
        
    def __str__(self): #this is what you see if you say "print(object)" #readable
        return self.__dict__

class Bayesian_pars():
    """
    Class for objects containing the parameters for Bayesian weighting.

    Expects to use the following equation for Bayesian weighting: (Haer et al., 2017)
    
                 [a*RP_t + b*I_experience + c*I_media + d*I_neighbours] 
    RP_t+1 =    --------------------------------------------------------
                                  [a + b + c + d]
    
    Convention for arguments a-d
    if list of length 1: this weighting factor always applies
    if list of length 2: list[0] = no flood; list[1] = flood
    if list of length 3: list[0] = no flood; list[1] = near miss; list[2] = flood
    
    Arguments:
        *a* (list of floats) : weighting factor for risk perception in the previous timestep
        *b* (list of floats) : weighting factor for flood experience in the current timestep
        *c* (list of floats) : weighting factor for impact of the media/science/other external influence
        *d* (list of floats) : weighting factor for experience in other regions
    
    """
    def __init__(self,a,b,c,d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
    
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