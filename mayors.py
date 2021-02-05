"""
This describes the mayors that can be used in the urban-SETP model

@author: Kees van Ginkel
github.com/keesvanginkel

"""

__author__ = '{Kees van Ginkel}'

import copy

#Own modules
from classes import *


#Factor which is only relevant if a more radical measure is proposed when they where
#still working on another (smaller) measure
measure_bonus_factor = 0.5 #fraction of the years of the smaller measure, that implementing 
                           #the new measure will go faster


class Reactive(Mayor):
    """
    Reactive management strategy:
    In case of near miss: implements a Small dike heightening
    In case of a flood event: implements a Large dike heightening
    
    """
    def get_name(self):
        return('R. Active')
    
    def get_full_name(self):
        return('mr. Ree Active')
    
    def paper_name(self):
        return('Reactive')
    
    def apply_strategy(self,Model,SurgeLevel,Measures,i,time):
        """
        Arguments:
            *Model* (Model object)
            *SurgeLevel* (SurgeLevel object)
            *Measures* (tuple of measures) = (small,large)
                tuple items are of type 'Measure_FloodProtection'
            *i* (int) : index of timestep
            *time* (list) : all years
            
        Effect of this method is that Measures will be implemented 
        in the model object after some lead time
        """
        #DRAW MEASURES FROM THE LIST
        small = Measures[0]
        large = Measures[1]
        
        #STRATEGY FOR THE OUTERDIKE AREA
        #TODO
        
        #STRATEGY FOR THE CITY CENTRE
        CC = Model.allResidentialArea[1]
        FP = Model.allFloodProtection[1] #the object to which to apply the heightening
        
        if CC.event_impact_history[i] == 10:
            #print('Small measure triggered', str(time[i]))
            #print(small.name, small.lead_time)
            #check if there are already measures planned
            newmeasure = copy.deepcopy(small) #make a copy of the measure to implement
            
            lst = [Measure for Measure in allactiveMeasure if Measure.apply_to.name == FP.name]
            #list is either empty or has an active object
            if len(lst) != 0: #if there is an active measure
                Measure_inprogress = lst[0]
                #IN THIS CASE WE DON'T NEED TO CHECK FURTHER! 
                #BECAUSE THIS IS THE SMALLEST MEASURE, 
                #AN EXISTING MEASURE WILL ALWAYS BE THE SAME OR LARGER THAN THE NEW IDEA!
            else: #there are no active measures
                newmeasure.plan_measure(FP,i)
            
        if CC.event_impact_history[i] > 10:
            #print('Large measure triggered')
            #check if there are already measures planned
            newmeasure = copy.deepcopy(large) #make a copy of the measure to implement
            
            lst = [Measure for Measure in allactiveMeasure if Measure.apply_to.name == FP.name]
            #list is either empty or has an active object
            if len(lst) != 0: #if there is an active measure
                measure_inprogress = lst[0]
                if newmeasure.heightening > measure_inprogress.heightening: #the new plan is larger than the old one
                    #print('A special situation occurs. The old plan was: {}'.format(measure_inprogress))
                    #print('The new plan is: {}'.format(newmeasure))
                    
                    #number of years they were already working on the old measure before they decided
                    #that they should give up and work on the new measures
                    already_working_on_it = measure_inprogress.lead_time - measure_inprogress.time_to_implementation
                    bonus = int(round(already_working_on_it*measure_bonus_factor,0)) #how much faster can the new measure go?
                    bonus = max(0,bonus) #bonus should never become smaller than 0 
                    
                    allactiveMeasure.remove(measure_inprogress) #remove the old measure from the active measure list
                    
                    #print('The bonus is: {}'.format(bonus))
                    newmeasure.lead_time = newmeasure.lead_time - bonus #you can implement the new plan faster!
                    #print('So the new planned measure is: {}'.format(newmeasure))
                    newmeasure.plan_measure(FP,i)
                    #print(allactiveMeasure)
   
            else: #there are no active measures
                newmeasure.plan_measure(FP,i)
    
class Lawkeeper(Mayor):
    """
    Management strategy that follows a the flood protection standards
    When the return period of the flood protection is below a threshold,
    action needs to be taken.
    """

    
    def get_name(self):
        return('Lawkeeper')
    
    def get_full_name(self):
        return('Ms. A.L.L. Lawkeeper')
    
    def paper_name(self):
        return('Proactive')
    
    def apply_strategy(self,Model,SurgeLevel,Measures,i,time):
        """
        Arguments:
            *Model* (Model object)
            *SurgeLevel* (SurgeLevel object)
            *Measures* (tuple of measures) = (small,large)
                tuple items are of type 'Measure_FloodProtection'
            *i* (int) : index of timestep
            *time* (int) : year of timestep
            
        Effect of this method is that Measures will be implemented 
        in the model object after some lead time
        """
        #DRAW MEASURES FROM THE LIST
        small = Measures[0]
        large = Measures[1]
        
        #The law prescripes the following thresholds
        self.threshold_small = 10000 #Underceedance threshold for implementing small upgrade return period (year)
        self.threshold_large = 2000 #Underceedance threshold for implementing large upgrade return period (year)
        
        #STRATEGY FOR THE OUTERDIKE AREA
        #NO STRATEGY FOR THE HEIJPLAAT
        
        #STRATEGY FOR THE INNERDIKE AREA
        CC = Model.allResidentialArea[1] #City Centre object
        FP = Model.allFloodProtection[1] #the object to which to apply the heightening
        
        if self.threshold_large < CC.protection_level_rp[i] <= self.threshold_small:
            #print('Small measure triggered')
            #check if there are already measures planned
            newmeasure = copy.deepcopy(small) #make a copy of the measure to implement
            
            lst = [Measure for Measure in allactiveMeasure if Measure.apply_to.name == FP.name]
            #list is either empty or has an active object
            if len(lst) != 0: #if there is an active measure
                Measure_inprogress = lst[0]
                #IN THIS CASE WE DON'T NEED TO CHECK FURTHER! 
                #BECAUSE THIS IS THE SMALLEST MEASURE, 
                #AN EXISTING MEASURE WILL ALWAYS BE THE SAME OR LARGER THAN THE NEW IDEA!
            else: #there are no active measures
                newmeasure.plan_measure(FP,i)
        
        if CC.protection_level_rp[i] <= self.threshold_large:
            #print('Large measure triggered')
            #check if there are already measures planned
            newmeasure = copy.deepcopy(large) #make a copy of the measure to implement
            
            lst = [Measure for Measure in allactiveMeasure if Measure.apply_to.name == FP.name]
            #list is either empty or has an active object
            if len(lst) != 0: #if there is an active measure
                measure_inprogress = lst[0]
                if newmeasure.heightening > measure_inprogress.heightening: #the new plan is larger than the old one
                    #print('A special situation occurs. The old plan was: {}'.format(measure_inprogress))
                    #print('The new plan is: {}'.format(newmeasure))
                    
                    #number of years they were already working on the old measure before they decided
                    #that they should give up and work on the new measures
                    already_working_on_it = measure_inprogress.lead_time - measure_inprogress.time_to_implementation
                    bonus = int(round(already_working_on_it*measure_bonus_factor,0)) #how much faster can the new measure go?
                    bonus = max(0,bonus) #bonus should never become smaller than 0 
                    
                    allactiveMeasure.remove(measure_inprogress) #remove the old measure from the active measure list
                    
                    #print('The bonus is: {}'.format(bonus))
                    newmeasure.lead_time = newmeasure.lead_time - bonus #you can implement the new plan faster!
                    #print('So the new planned measure is: {}'.format(newmeasure))
                    newmeasure.plan_measure(FP,i)
                    #print(allactiveMeasure)
   
            else: #there are no active measures
                newmeasure.plan_measure(FP,i)            

class Economicus(Mayor):
    """
    Management strategy on the basis of a cost-benefit rationality
    
    """
    
    def get_name(self):
        return('H. Economicus')

    def get_full_name(self):
        return('Mr. H. Economicus')
    
    def paper_name(self):
        return('Economic')
    
    def apply_strategy(self,Model,SurgeLevel,Measures,i,time):
        """
        Arguments:
            *Model* (Model object)
            *SurgeLevel* (SurgeLevel object)
            *Measures* (tuple of measures) = (small,large)
                tuple items are of type 'Measure_FloodProtection'
            *i* (int) : index of timestep
            *time* (int) : year of timestep
            
        Effect of this method is that Measures will be implemented 
        in the model object after some lead time
        """
        #We assume that from CBA follow these threshold (mln euro per year)
        self.threshold_small = 5 #Underceedance threshold for implementing small upgrade return period (year)
        self.threshold_large = 10 #Underceedance threshold for implementing large upgrade return period (year)
        
        
        #DRAW MEASURES FROM THE LIST
        small = Measures[0]
        large = Measures[1]
        
        #STRATEGY FOR THE CITY CENTRE
        CC = Model.allResidentialArea[1]
        FP = Model.allFloodProtection[1] #the object to which to apply the heightening

        if self.threshold_small <= CC.risk[i] < self.threshold_large: #If the flood risk in the City Centre exceeds X mln euro per year
            newmeasure = copy.deepcopy(small) #make a copy of the measure to implement    
            lst = [Measure for Measure in allactiveMeasure if Measure.apply_to.name == FP.name]
            #list is either empty or has an active object
            if len(lst) != 0: #if there is an active measure
                Measure_inprogress = lst[0]
                #IN THIS CASE WE DON'T NEED TO CHECK FURTHER! 
                #BECAUSE THIS IS THE SMALLEST MEASURE, 
                #AN EXISTING MEASURE WILL ALWAYS BE THE SAME OR LARGER THAN THE NEW IDEA!
            else: #there are no active measures
                newmeasure.plan_measure(FP,i)

        elif CC.risk[i] >= self.threshold_large: #If the flood risk in the City Centre exceeds X mln euro per year
            newmeasure = copy.deepcopy(large) #make a copy of the measure to implement
            
            lst = [Measure for Measure in allactiveMeasure if Measure.apply_to.name == FP.name]
            #list is either empty or has an active object
            if len(lst) != 0: #if there is an active measure
                measure_inprogress = lst[0]
                if newmeasure.heightening > measure_inprogress.heightening: #the new plan is larger than the old one
                    #print('A special situation occurs. The old plan was: {}'.format(measure_inprogress))
                    #print('The new plan is: {}'.format(newmeasure))
                    
                    #number of years they were already working on the old measure before they decided
                    #that they should give up and work on the new measures
                    already_working_on_it = measure_inprogress.lead_time - measure_inprogress.time_to_implementation
                    bonus = int(round(already_working_on_it*measure_bonus_factor,0)) #how much faster can the new measure go?
                    bonus = max(0,bonus) #bonus should never become smaller than 0 
                    
                    allactiveMeasure.remove(measure_inprogress) #remove the old measure from the active measure list
                    
                    #print('The bonus is: {}'.format(bonus))
                    newmeasure.lead_time = newmeasure.lead_time - bonus #you can implement the new plan faster!
                    #print('So the new planned measure is: {}'.format(newmeasure))
                    newmeasure.plan_measure(FP,i)
                    #print(allactiveMeasure)
   
            else: #there are no active measures
                newmeasure.plan_measure(FP,i)

class Economicus_HP_iter(Mayor):
    """
    Management strategy on the basis of a cost-benefit rationality
    
    In addition to the normal behaviour of economicus, this mayor will implement a measure on the Heijplaat.
    
    """
    
    def get_name(self):
        return('H. Economicus_iter')

    def get_full_name(self):
        return('Mr. H. Economicus HP iterations')
    
    def paper_name(self):
        return('Economic_iter')
    
    def apply_strategy(self,Model,SurgeLevel,Measures,i,time):
        """
        Arguments:
            *Model* (Model object)
            *SurgeLevel* (SurgeLevel object)
            *Measures* (tuple of measures) = (small,large)
                tuple items are of type 'Measure_FloodProtection'
            *i* (int) : index of timestep
            *time* (int) : year of timestep
            
        Effect of this method is that Measures will be implemented 
        in the model object after some lead time
        """
        #We assume that from CBA follow these threshold (mln euro per year)
        self.threshold_small = 5 #Underceedance threshold for implementing small upgrade return period (year)
        self.threshold_large = 10 #Underceedance threshold for implementing large upgrade return period (year)
        
        
        #DRAW MEASURES FROM THE LIST
        small = Measures[0]
        large = Measures[1]
        
        
        #STRATEGY FOR THE HEIJPLAAT
        HP = Model.allResidentialArea[0] #Select the Heijplaat Residential Area object
        
        if hasattr(HP,'flood_proofing'): #Guarantee backward compat. (20 aug)
            if HP.risk[i] > 0.5: #implement measure if risk gets above certain threshold
                HP.flood_proofing[i:] = [True] * len(HP.flood_proofing[i:])
                #print('measure implemented in i={} and time={}'.format(i,time[i]))
            
        
        #STRATEGY FOR THE CITY CENTRE
        CC = Model.allResidentialArea[1]
        FP = Model.allFloodProtection[1] #the object to which to apply the heightening

        if self.threshold_small <= CC.risk[i] < self.threshold_large: #If the flood risk in the City Centre exceeds X mln euro per year
            newmeasure = copy.deepcopy(small) #make a copy of the measure to implement    
            lst = [Measure for Measure in allactiveMeasure if Measure.apply_to.name == FP.name]
            #list is either empty or has an active object
            if len(lst) != 0: #if there is an active measure
                Measure_inprogress = lst[0]
                #IN THIS CASE WE DON'T NEED TO CHECK FURTHER! 
                #BECAUSE THIS IS THE SMALLEST MEASURE, 
                #AN EXISTING MEASURE WILL ALWAYS BE THE SAME OR LARGER THAN THE NEW IDEA!
            else: #there are no active measures
                newmeasure.plan_measure(FP,i)

        elif CC.risk[i] >= self.threshold_large: #If the flood risk in the City Centre exceeds X mln euro per year
            newmeasure = copy.deepcopy(large) #make a copy of the measure to implement
            
            lst = [Measure for Measure in allactiveMeasure if Measure.apply_to.name == FP.name]
            #list is either empty or has an active object
            if len(lst) != 0: #if there is an active measure
                measure_inprogress = lst[0]
                if newmeasure.heightening > measure_inprogress.heightening: #the new plan is larger than the old one
                    #print('A special situation occurs. The old plan was: {}'.format(measure_inprogress))
                    #print('The new plan is: {}'.format(newmeasure))
                    
                    #number of years they were already working on the old measure before they decided
                    #that they should give up and work on the new measures
                    already_working_on_it = measure_inprogress.lead_time - measure_inprogress.time_to_implementation
                    bonus = int(round(already_working_on_it*measure_bonus_factor,0)) #how much faster can the new measure go?
                    bonus = max(0,bonus) #bonus should never become smaller than 0 
                    
                    allactiveMeasure.remove(measure_inprogress) #remove the old measure from the active measure list
                    
                    #print('The bonus is: {}'.format(bonus))
                    newmeasure.lead_time = newmeasure.lead_time - bonus #you can implement the new plan faster!
                    #print('So the new planned measure is: {}'.format(newmeasure))
                    newmeasure.plan_measure(FP,i)
                    #print(allactiveMeasure)
   
            else: #there are no active measures
                newmeasure.plan_measure(FP,i)            
        
        
class Sentiment(Mayor):
    """
    Management strategy on the basis of a cost-benefit rationality
    
    """
    
    #TODO: THRESHOLDS AS ATTRIBUTES OF THE CLASS
    
    def get_name(self):
        return('Sentiment')

    def get_full_name(self):
        return('Mr. Peter Sentiment')    
    
    def paper_name(self):
        return('Sentiment')
    
    def apply_strategy(self,Model,SurgeLevel,Measures,i,time):
        """
        Arguments:
            *Model* (Model object)
            *SurgeLevel* (SurgeLevel object)
            *Measures* (tuple of measures) = (small,large)
                tuple items are of type 'Measure_FloodProtection'
            *i* (int) : index of timestep
            *time* (int) : year of timestep
            
        Effect of this method is that Measures will be implemented 
        in the model object after some lead time
        """
        #DRAW MEASURES FROM THE LIST
        small = Measures[0]
        large = Measures[1]
        
        #STRATEGY FOR THE CITY CENTRE
        CC = Model.allResidentialArea[1]
        FP = Model.allFloodProtection[1] #the object to which to apply the heightening

        if 5 <= CC.risk_perceived[i] < 10: #If the perceived flood risk in the City Centre exceeds X mln euro per year
            newmeasure = copy.deepcopy(small) #make a copy of the measure to implement    
            lst = [Measure for Measure in allactiveMeasure if Measure.apply_to.name == FP.name]
            #list is either empty or has an active object
            if len(lst) != 0: #if there is an active measure
                Measure_inprogress = lst[0]
                #IN THIS CASE WE DON'T NEED TO CHECK FURTHER! 
                #BECAUSE THIS IS THE SMALLEST MEASURE, 
                #AN EXISTING MEASURE WILL ALWAYS BE THE SAME OR LARGER THAN THE NEW IDEA!
            else: #there are no active measures
                newmeasure.plan_measure(FP,i)

        elif CC.risk_perceived[i] >= 10: #If the perceived flood risk in the City Centre exceeds X mln euro per year
            newmeasure = copy.deepcopy(large) #make a copy of the measure to implement
            
            lst = [Measure for Measure in allactiveMeasure if Measure.apply_to.name == FP.name]
            #list is either empty or has an active object
            if len(lst) != 0: #if there is an active measure
                measure_inprogress = lst[0]
                if newmeasure.heightening > measure_inprogress.heightening: #the new plan is larger than the old one
                    #print('A special situation occurs. The old plan was: {}'.format(measure_inprogress))
                    #print('The new plan is: {}'.format(newmeasure))
                    
                    #number of years they were already working on the old measure before they decided
                    #that they should give up and work on the new measures
                    already_working_on_it = measure_inprogress.lead_time - measure_inprogress.time_to_implementation
                    bonus = int(round(already_working_on_it*measure_bonus_factor,0)) #how much faster can the new measure go?
                    bonus = max(0,bonus) #bonus should never become smaller than 0 
                    
                    allactiveMeasure.remove(measure_inprogress) #remove the old measure from the active measure list
                    
                    #print('The bonus is: {}'.format(bonus))
                    newmeasure.lead_time = newmeasure.lead_time - bonus #you can implement the new plan faster!
                    #print('So the new planned measure is: {}'.format(newmeasure))
                    newmeasure.plan_measure(FP,i)
                    #print(allactiveMeasure)
   
            else: #there are no active measures
                newmeasure.plan_measure(FP,i)
