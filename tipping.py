"""
This script contains all classes and functions for exploring tipping points in the experiments.
which can be explored

@author: Kees van Ginkel
github.com/keesvanginkel

"""

__author__ = '{Kees van Ginkel}'

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from matplotlib import patches
from matplotlib.collections import PatchCollection

class Metric():
    """
    Indicates which model outcome parameters should be considered model metrics
    
    Properties:
    (upon initialization):
        *self.name* (string) : name of the metric
        *self.raw* (Pandas Series) : year as index, metric value as value
        
    (upon create_statistics):
        *self._window* (int) : size of the rolling windows, not meant to be altered
        *self.statistics* (Pandas DataFrame) : columns are statistics of the metric
        
    (upon find_SETP_candidates):
        *self._margin* (int) : margin around window to search for stable states, not meant to be altered
        *self.allSETPs_cands* (list) : list of SETP-objects in metric
        *self.stable_states* (list) : all stable states in metric
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
    
    def create_statistics(self,window,domain='All'):
        """
        Create statistics for Panda Series, used for tipping point analysis
        This sets the size of the rolling window: result is set to the right edge of the window
        if Cut = true: don't show rows containing al NaNs
        
        Arguments:
            *self.statistics* (Dataframe) : columns are statistics of the metric
            *_window* (int) : Width of the rolling window (in model timesteps, e.g. 4 year)

            *domain* (tuple) : tuple indicating the beginning and end year to include in the statistic
            
        Returns:
            *self.statistics* (DataFrame) : 
        """
        #set window as unmutable property
        self._window = window
        
        #Construct empty df to store results
        series = self.raw
        df = pd.DataFrame(index=series.index,data=series)
        
        #Calculate derivates of raw time series
        df["{}".format("First order derivative (dM/dt)")] = series.to_frame().diff()
        df["{}".format("Second order derivative (d2M/dt2)")] = series.to_frame().diff().diff()

        #Calculate statistics using a rolling window
        rolling = series.rolling(window=self._window)
        df["{}".format("Window mean")] = rolling.mean()
        df["{}".format("Window variance")] = rolling.var()

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
    
    def find_SETP_candidates(self,c1,c2,c3,margin):
        """
        Find the SETPs for a Metric timeseries, based on the statistics of this metric and tipping point
        criteria.

        This function will replace the select_candidates function.

        This function is to be run after the create_statistics function.


        Arguments:
            *c1* (float) : absolute change of house price as fraction of house price at t0: detect rapid change
            *c2* (float) : absolute valued threshold for variance: detect stable states
            *c3* (float) : percentage of change between states: substantially different states
            *margin* (int) : margin around TP for assessing stable states (in model timesteps e.g. 2 years)
         
        Uses
            *self._window* (int) : window size for functionality using a moving window 
                        ... set in create_statistics

        Effect of the function:

        adds attributes to the metric:
            self.allSETPs_cands (list of SETP-objects) : 
            self.stable_states (list of stable states)
            
        Removed on 15/2: c1=0.15,c2=0.2e10,c3=10,margin=2

        """
        #set margin as unmutable property
        self._margin = margin
        
        ind = self.statistics.index
        df = pd.DataFrame(index=ind) #save some in-between results in a df

        self.allSETPs_cands = [] #save everything that looks like an SETP

        #######################################
        # CRITERION 1: CHECK FOR RAPID CHANGE #
        #######################################

        house_price_t0 = self.raw.iloc[0]

        #negative change
        df["rapid change_neg"] = pd.Series(index=ind,data=[-1]*len(ind)) \
                [(self.statistics["First order derivative (dM/dt)"] <= -c1* house_price_t0)]
        #positive change
        df["rapid change_pos"] = pd.Series(index=ind,data=[1]*len(ind)) \
                [(self.statistics["First order derivative (dM/dt)"] >= +c1* house_price_t0)] 
        #Concat change values values
        df['rapid change'] = pd.concat([df['rapid change_neg'].dropna(),df['rapid change_pos'].dropna()])
        #CREATE SETP OBJECTS FOR ALL TIMESTEPS WITH RAPID CHANGE
        for index,value in df['rapid change'].items():
            if not np.isnan(value): #this is a relevant value  
                self.allSETPs_cands.append(SETP(index,int(value))) #creates SETP objects with year and sign

        ##########################################
        # CRITERION 2: CHECK FOR STATE STABILITY #
        ##########################################

        df["stable"] = pd.Series(index=ind,data=[2]*len(ind))[self.statistics["Window variance"] < c2]

        #The self.candidates originates from the select_candidates functions, TODO: this should be done by this function
        self.stable_states = find_states(df['stable'],self._window,2.0) #returns begin and end years of stable states

        #Adds stable state before and after the SETP to the SETP object
        for cand in self.allSETPs_cands:
            before, after = find_window_around_point(cand.year,self.stable_states,
                                                     window_size=self._window,margin=self._margin,index=True)    
            #before and after are the indices of the states before and after; or None
            cand.before = before
            cand.after = after    

        #Add information on duplicates (if any)
        self.allSETPs_cands = identify_duplicates(self.allSETPs_cands)

        #If the window before equals the window after, set SETP type at 'sw' = 'same_window'
        for i, cand in enumerate(self.allSETPs_cands):
            if cand.before == cand.after:   #before and after windows are similar
                cand.Type = 'sw' 

        ##CLASSIFYING REMAINING EXAMPLES
        for i, cand in enumerate(self.allSETPs_cands):
            if not cand.Type == 'sw': #don't check if already assigned 'same window'
                    if cand.before is not None: #stable state before point
                        if cand.after is not None: #stable state after point
                            cand.Type = 'real'
                        else: #stable before, but not after
                            cand.Type = 'ob'
                    else: #no stable state before point
                        if cand.after is not None: #not stable before, but stable after
                            cand.Type = 'oa'
                        else: 
                            cand.Type = 'no'
                            
        #########################################################
        # CRITERION 3: CHECK FOR SUBSTANTIALLY DIFFERENT STATES #
        #########################################################     

        #This part of the algorithm was changed on 19 jan 2021. Initially, the difference between the states
        #was derived by comparing the last house price in state A with the first house price in state B.
        #In the updated version, the mean of both states are compared.

        for i, cand in enumerate(self.allSETPs_cands):
            if cand.Type == 'real': #only check for the ones that meet C1 and C2

                timeseries = self.statistics.iloc[:,0]
                mean_of_states_dict, as_df = mean_of_states(self.stable_states, timeseries)

                mean_state_before = mean_of_states_dict[cand.before]
                mean_state_after = mean_of_states_dict[cand.after]
                difference = mean_state_after - mean_state_before
                if not mean_state_before == 0:
                    perc_diff = 100 * abs(difference / mean_state_before)
                    if perc_diff <= c3: cand.Type = 'us' #indicate that there is an unsubstantial difference
                else: cand.Type = 'zd' #indicate that there is zero-division

                #THIS IS THE OLD VERSION (BEFORE 19 JAN 2021)
                #end_state_before = self.stable_states[cand.before][1] #last year of previous state
                #last_house_price_stateA = self.statistics.loc[end_state_before].iloc[0]
                #start_state_after = self.stable_states[cand.after][0] #first year of next state
                #first_house_price_stateB = self.statistics.loc[start_state_after].iloc[0]
                #difference = last_house_price_stateA - first_house_price_stateB
                #perc_of_A = abs(100 * difference / last_house_price_stateA)
                #perc_of_B = abs(100 * difference / first_house_price_stateB)
                #if (perc_of_A <= c3) or (perc_of_B <= c3): #difference is not substantial enough
                #    cand.Type = 'us' #unsubstantial difference between before and after
                    

        self.candidates = df #save some of the converted statistics as a df to make the plotting easier
        
    def select_SETPs(self,sign,add_stable_after=False,add_stable_before=False,add_unsubstantial=False):
        """
        Select a subgroup of SETPs from candidates
        
        This should be run after find_setp_candidates
        
        Arguments:
            *sign* (int) : -1 or 1, indicating positive or negative 'rapid changes'
            *add_stable_after* (bool) : add cands which are only stable after the rapid change (type 'oa')
            *add_stable_before* (bool) : add cands which are only stable before the rapid change (type 'ob')
            *add_unsubstantial* (bool) : add cands which states before are not substantially different
                                         from the state after (type 'us')
        
        Effect:
            creates self.selected_SETPs (list) : sequence of SETP objects
        
        """
        
        sel_cands = [setp for setp in self.allSETPs_cands if setp.sign == sign]

        selected_examples_years = [setp.year for setp in sel_cands if setp.Type == 'real' and setp.duptype != 'dup']
        duplicates_years = [setp.year for setp in sel_cands if setp.duptype == 'dup']
        only_after = [setp.year for setp in sel_cands if setp.Type == 'oa']
        only_before = [setp.year for setp in sel_cands if setp.Type == 'ob']
        same_window = [setp.year for setp in sel_cands if setp.Type == 'sw']
        not_before_not_after = [setp.year for setp in sel_cands if setp.Type == 'no']
        unsubstantial = [setp.year for setp in sel_cands if setp.Type == 'us']


        #MANUALLY ADD THE POSITIVE SETPS IF THEY HAVE A NEGATIVE DUPLICATE
        additions = [] #save the ones that are still relevant
        positives = [setp for setp in self.allSETPs_cands if setp.sign == 1 and setp.duptype == 'dup_first']
        #the above are positives with duplicates (these duplicates might be negative, so still relevant)
        for positive in positives:
            n = 0
            for duplicate_year in positive.dups_with:
                duplicate = [setp for setp in self.allSETPs_cands if setp.year == duplicate_year][0]
                if duplicate.sign == sign and duplicate.Type == 'real':
                    if n < 1: #make sure only the first one is added
                        additions.append(duplicate) #but not all, only the first!
                        n += 1

        for setp in additions:
            selected_examples_years.append(setp.year)
            
        self.selected_SETPs = selected_examples_years[:]
        
        #Todo: save as a dict
        self.candidates_as_lists = (self.selected_SETPs,duplicates_years,only_after,
                only_before,same_window,not_before_not_after,unsubstantial)
        
    def plot_SETPs(self,**kwargs):
        """
        Plot the results
        
        This should be run after select_SETPs
        
        Arguments:
            **kwargs** () : will be passed to plt.subplots()
        
        
        
        
        Returns:
            fig,ax (matplotlib objects)
        
        """
        #Update (15/2/2021)
        #*self._window* (int) :, is inferred from earlier definition window size in years; also _margin
        if not hasattr(self, '_window'):
            raise AttributeError('Window Metric._window is not defined, call Metric.create_statistics() first')
        if not hasattr(self, '_margin'):
            raise AttributeError('Margin Metric._margin is not defined, call Metric.find_SETP_candidates() first')
        
        window = self._window
        margin = self._margin
        
        #get the output of the select_SETPs functions (this is not exactly the same as 
        #just the candidates, because we selected on sign)
        selected_SETPs,duplicates_years,only_after,only_before, \
            same_window,not_before_not_after, unsubstantial = self.candidates_as_lists
        
        fig, ax = plt.subplots(nrows=2,**kwargs)
        col = self.statistics.columns[0]
        self.statistics[col].plot(ax=ax[0])
        timeseries = self.statistics[col]

        ### PLOT STABLE STATES AS SHADED AREAS ###
        #Windows have length 'window'
        #shading starts at - window t

        #Add all not-nan values as a starting point for a box
        boxes_left = []
        series = self.candidates['stable']
        for index,value in series.items():
            if not np.isnan(value): #this is a relevant value
                boxes_left.append(index)   
        boxes_left

        patches_list=[]
        for year in boxes_left:
            art = patches.Rectangle((year-window,- 25_000),window,400_000)
            patches_list.append(art)

        pc = PatchCollection(patches_list,facecolor='grey',alpha=0.15)
        ax[0].add_collection(pc)


        ### PLOT TIPPING POINTS
        #replace the value -1 or 1 with the house price in that timestep 
        for index,value in self.candidates['rapid change_pos'].items():
            if not np.isnan(value):
                self.candidates['rapid change_pos'].at[index] = timeseries.at[index] 

        for index,value in self.candidates['rapid change_neg'].items():
            if not np.isnan(value):
                self.candidates['rapid change_neg'].at[index] = timeseries.at[index] 

        ((self.candidates['rapid change_neg'].loc[2020:2200])).plot(style='v',ax=ax[0],markersize=15,markerfacecolor='red')
        ((self.candidates['rapid change_pos'].loc[2020:2200])).plot(style='^',ax=ax[0],markersize=15,markerfacecolor='green')
        
        ax[0].set_title('Criterion 1: Rapid change')
        #ax[0].set_xlabel('Time (years)')
        ax[0].set_ylabel('House price (€)')
        
        
        def add_patch(legend):
            from matplotlib.patches import Patch
            ax = legend.axes

            handles, labels = ax.get_legend_handles_labels()
            handles.append(Patch(facecolor='grey', edgecolor=None))
            labels.append("Variance in window below threshold C2")

            legend._legend_box = None
            legend._init_legend_box(handles, labels)
            legend._set_loc(legend._loc)
            legend.set_title(legend.get_title().get_text())

        lgd = ax[0].legend()
        add_patch(lgd)
        
        #ax[0].legend()
        
        
        ### Plot states
        self.stable_states = find_states(self.candidates['stable'],window,2.0) #returns begin and end years of stable states
        #for i,state in enumerate(self.stable_states):
        #    x_values = list(range(state[0],state[1]+1))
        #    y_value = 2
        #    ax[1].plot(x_values,[y_value]*len(x_values))
        #    ax[1].text(sum(x_values)/len(x_values),y_value,str(i))
        



        perfect_example_years = selected_SETPs
        
        ### PLOT PERFECT EXAMPLES
        ax[1].scatter(perfect_example_years,[300_000]*len(perfect_example_years),s=150,color='black',label='Stable before and after the rapid change')
        ax[1].scatter(unsubstantial,[300_000]*len(unsubstantial),s=150, marker='s',color='gold', label='No substantial difference between states')
        ax[1].scatter(only_after,[200_000]*len(only_after),s=150,color='red',marker=9,label='Only stable after the rapid change') #(CARETRIGHTBASE)
        ax[1].scatter(only_before,[200_000]*len(only_before),s=150,color='blue',marker=8,label='Only stable before the rapid change') # (CARETLEFTBASE)

        ax[1].scatter(duplicates_years,[100_000]*len(duplicates_years),s=150,color='grey',label='Duplicates',marker="P")
        ax[1].scatter(same_window,[100_000]*len(same_window),s=150,color='grey',label='Same state',marker="D")
        ax[1].scatter(not_before_not_after,[100_000]*len(not_before_not_after),s=150,color='grey',label='Unstable before and after',marker="X")
        


        ### CRITERION 3: SUBSTANTIAL DIFFERENT STATES
        as_dict, as_df = mean_of_states(self.stable_states,timeseries)

        col = self.statistics.columns[0]
        self.statistics[col].plot(ax=ax[1],style='--',color='grey',alpha=0.5)

        for i,state in enumerate(self.stable_states):
            x_values = list(range(state[0],state[1]+1))
            y_value = as_dict[i]
            if i == 0: #only for first item, prepare legend item
                ax[1].plot(x_values,[y_value]*len(x_values),lw=3,label='Stable state')
            else: 
                ax[1].plot(x_values,[y_value]*len(x_values),lw=3)
            ax[1].text(sum(x_values)/len(x_values),y_value,str(i))
        
        ax[1].legend()
        ax[1].set_xlabel('Time (years)')
        ax[1].set_ylabel('House price (€)')
        ax[1].set_title('Criterion 2: Stable states, Criterion 3: Substantially different states')
            
        return fig,ax

class SETP():
    "A socio-economic tipping point candidate"
    
    def __init__(self,year,sign):
        self.year = year
        self.sign = sign #can be +1 or -1 (int)
        self.Type = None
        self.duptype = None
    
    
    def set_Type(self,Type):
        """
        None : not set
        'real' : real tipping point 
        'sw' : window before = window after (no state shift)
        'dup' : duplicate of another!
        'dup_first' : has duplicates, but this is the first of them
        'oa' : only stable after point
        'ob' : only stable before point
        'no' : not stable before and not stable after point
        
        """
        self.Type = Type 
        
    def __repr__(self):
        if hasattr(self,'dups_with'):
            extra = " -dups with: (" + str(self.dups_with).strip('[]') + ')'
        else:
            extra = "_"
        return str(self.year) + '__' + str(self.sign) + '__' + str(self.Type) + '__' + str(self.duptype) + extra 
        


class state():
    """
    Stable state
    """
    
    def __init__(self,i,start,end):
        self.i = i #identifier
        self.start = start #
        self.end = end       

def average_before_after(data,year,window,margin):
    before = data.loc[year-margin-window:year-margin].mean()
    after = data.loc[year+margin:year+margin+window].mean()
    return(before,after)

def identify_duplicates(candidate_SETPs):
    """Identify duplicates in a list of SETP candidates
    Duplicate is a pair of SETPs that describe the same
    shift from state A to state B
    
    Arguments:
        *candidate_SETPs* (list of SETP objects)
    
    Returns: 
        *candidate_SETPs* (list of SETP objects)
        
    Effect:
        *change the self.Type of the SETP object* 
        If this is the first duplicate in a series:
        Type = 'dup_first'
        
        If it is a duplicate but not the first:
        Type = 'dup'
        
        For the first duplicate, it also adds a new attribute to the SETP object
        self.dups_with = [yeardup1, yeardup2] etc.    
    
    """
    setps = [s for s in candidate_SETPs]
    
    for i,setp_i in enumerate(setps):
        for setp_j in setps[i+1::]:
                if setp_i.before == setp_j.before and setp_i.after == setp_j.after: #duplicate!
                    if not setp_i.duptype == 'dup': # is not already a dup of an earlier setp itself
                        setp_i.duptype = 'dup_first'
                        if hasattr(setp_i,'dups_with'):
                            setp_i.dups_with.append(setp_j.year) #already has a list with dups
                        else:
                            setp_i.dups_with = [setp_j.year] #create a dups_with list  
                    setp_j.duptype = 'dup'
    return setps

def mean_of_states(states,series):
    """
    For each state, calculate the mean of the values in 
    the state describe in some series
    
    Arguments:
        *states* (list of tuples) : (start_year,end_year)
        *series* (Pandas Series) : the variable of interest to take the mean over (index=year)
        
    Returns:
        *mean_of_state* (Pandas Series) : (index=year), the means over each state
    """
    mean_of_states = pd.Series(index=series.index,dtype='float64')
    asdict = {}
    for i, state in enumerate(states):
        selection = series.loc[state[0]:state[1]]
        mean = selection.mean()
        asdict[i] = mean
        for j in range(state[0],state[1]+1):
            mean_of_states.at[j] = mean
    return asdict, mean_of_states

def find_states(sample,window,findvalue):
    """
    Finds and seperate states in a series
    
    Arguments:
        *sample* (Panda Series) : index = years, values = items of interest
        *window* (int) : size of the window 
        *findvalue* (flaot/int) : the value to find in the sample
    
    Returns:
        *states* (list of tuples) : each tuple contains start and end-year of the value of interest
    
    It assumes that sample was created using a moving window, the result of which is saved at 
    the last (most right) year that is still part of the window.
    
    """
    states = [] #keep the states here, save them as a tuple (start:end)  
    start_period = None
    end_period = None
    for index,value in sample.items():
        if value == findvalue:
            if start_period is None: #no period started, make new one
                start_period = index
            end_period = index #always equate end of period to the last value
        else:
            if start_period is not None and start_period is not None:
                states.append((start_period-window+1,end_period)) #append a new tuple to the states
                #the above also correct for the width of the window
                start_period = None #and create a new empty period
                end_period = None
    return states


def find_window_around_point(point, windows, window_size, margin, index=True):
    """
    Determine if there are stable windows around a certain point
    Todo: what also can be done, is not looking at a single point a certain distance, but iterating over [0:margin]
    Todo: distances from the point and select any of the detected value. Would probably not make a differnce for the
    Todo: current parameters settings, because margin < window_size.

    Arguments:
        *point* (int) : the year of interest
        *windows* (list of tuple): each list items is a state, described in tuple(start,end) of window
        *window_size* (int) : indicate the length of your window (unused)
        *margin* (int) : the number of distances one should look around the point for a windows

    Returns:
        if index = True:
        (before,after) : indices of the windows before and after, contains None if no window could be found
        if index = False:
        return the windows themselves
    """

    before = None
    after = None

    # Look before the point
    for i, window in enumerate(windows):
        if point - margin >= window[0]:
            if point - margin <= window[1]:
                before = window
                if index: before = i

    # Look after the point
    for i, window in enumerate(windows):
        if point + margin >= window[0]: # (15/2/2021 removed + window_size)
            if point + margin <= window[1]: # (15/2/2021 removed + window_size)
                after = window
                if index: after = i

    return before, after

def add_suptitle(fig, exp, M):
    """Add some information about the experiment as title to a figure created with M.plot_SETPs

    Arguments:
        fig (Matplotlib Figure) : Figure created with M.plot_SETPs
        exp : experiment object from which to draw the metadata
        metric : the metric from which to draw the metadata

    Returns:
        fig (Matplotlib Figure) : the input figure with a suptitle

    """

    # Make the data of the experiment more readable before sending it to the string
    housing_market = M.name.split('_')[-1]
    if housing_market == 'subj':
        housing_market = 'Boundedly rational'
    else:
        housing_market = 'Rational'

    area_name = M.name.split('_')[1]
    if area_name == 'A':
        area_name = 'A (Heijplaat, outer-dike)'
    else:
        area_name = 'B (City Centre, inner-dike)'

    # Create the title string
    suptitle_string = ( \
        '''Sea level rise scenario: {} ||| Storm surge series: {} ||| Mayor: {}
        {} housing market ||| Area {}'''.format(
            exp.SurgeLevel.corresponding_SLR_Scenario.name.split('_')[-1],
            exp.SurgeLevel.corresponding_SurgeHeight.name.split('_')[-1],
            exp.Mayor.get_name(),
            housing_market,
            area_name))
    fig.suptitle(suptitle_string)

    file_string = exp.SurgeLevel.corresponding_SLR_Scenario.name.split('_')[-1] + '_' + \
                  exp.SurgeLevel.corresponding_SurgeHeight.name.split('_')[-1] + '_' + \
                  exp.Mayor.get_name() + '_' + M.name.split('_')[-1] + '_' + M.name.split('_')[1]
    return fig, file_string