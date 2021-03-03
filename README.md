# Urban-SETP

This repository contains the model code and documentation for the paper Ginkel, Haasnoot & Botzen (2021, under review): "A framework for identifying climate change induced socio-economic tipping points".

The model is a highly stylized, archetypical description of flood risk to the City of Rotterdam, under many possible futures and dynamic adaptive flood protection strategies. It is meant to illustrate the identification of tipping points from a large number of experiments, not for detailed forecasting of the actual system state.

The main uncertainties are:
 - Sea level rise scenarios
 - Storm surge scenarios
 - The flood protection strategy (reflected by a 'mayor')
 - The time it takes to implement flood protection measures
 - The behaviour of the housing market in response to the flood risk

# Quick tour and key results
Here, we take you through the basic, default model set-up and show some key figures.<br /><br />


## The model
The figure depicts the physical model components. It shows a coastal city, threatened by storm surges from the sea which are aggravated by sea level rise. Residential area A is an outer-dike area with an elevation well above sea level. Residential area B is located in a polder below sea level, but is protected by a dike. 

![]("/Drawings/Rotty.dio.png")

The model simulates the development of the flood risk over time for the residential areas of the city, for a variety of sea level rise and storm surge scenarios. The objective is to identify potential socio-economic tipping points. Four different management strategies (mayors) can be chosen to adapt components of the city or the flood protection over time. Each mayor reflects an archetypical, different approach to flood risk management.
The model runs on a yearly timestep, from 2020 to 2220. In each timestep t, the following steps are taken:
	The degree of sea level rise is determined from the climate scenario, and a storm surge level is drawn from the extreme value distribution 
	The water levels are compared to the flood protection levels, resulting in either ‘nothing happens’, a ‘near-miss wake-up call’ or a ‘flood’.  When the dikes are overtopped the resulting flood depths are calculated. Failure due to fragility of the dikes is not considered here
	A (objective) flood risk assessment for the sea level and storm surge conditions is carried out to calculate the annual expected damage for the climatic conditions in the timestep. This accounts for the SLR and adaptation that already took place until that timestep, but not for future SLR or adaptation 
	The recent experiences with floods (including near-misses) per residential area feed (together with some other factors outlined below) into the risk perception module, which calculates the development of the perceived or subjective flood risk as a function of the objective flood risk 
	Both the objective and subjective flood risk are discounted in the house price using hedonistic price theory
	The mayor of the city evaluates the above state parameters and decides on the implementation of new measures to manage the flood risk of the city 
	When their implementation time has expired, the measures contribute to the flood protection of the city.
A schematic overview of the model components is shown below.

![]("/Drawings/XXXX")

Notebook [00] shows the model behaviour for illustrative mayors and flood protection strategies.
Notebook [01] shows the model behaviour for different storm surge scenarios.
Notebook [02] shows the model behaviour for different implementation times.

## Tipping point identification
One of the objectives is to identi