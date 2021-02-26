# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 14:20:20 2021

@author: rahul
"""

import pandas as pd
import ast
from Market_clearing import Market_clearing
#%% Case data

Setpoint_P = pd.read_csv('Data_Files\Setpoint_P.csv',index_col='Time_target',converters={1:ast.literal_eval}) # Baseline injections at each node (negative for retrieval)
Setpoint_Q  = pd.read_csv('Data_Files\Setpoint_Q.csv',index_col='Time_target',converters={1:ast.literal_eval})

Setpoint=pd.DataFrame([], columns=['Setpoint_P','Setpoint_Q'], index=Setpoint_P.index)

for t in Setpoint_P.index:
    Setpoint.at[t,'Setpoint_P']=Setpoint_P.at[t,'Setpoint_P']
    Setpoint.at[t,'Setpoint_Q']=Setpoint_Q.at[t,'Setpoint_Q']
    
# Index for nodes
bus = pd.read_excel(open('Data_Files/network15bus.xlsx', 'rb'),sheet_name='Bus',index_col=0)
nodes = list(bus.index)

# Upload bids
all_bids = pd.read_csv('Data_Files\Bids.csv',index_col='ID')

# Create empty dataframes to contain the bids that were not matched (order book)
orderbook_offer = pd.DataFrame(columns = ['ID','Bus','P_or_Q','Direction','Quantity','Price','Time_target','Time_stamp'])
orderbook_offer.set_index('ID',inplace=True)
orderbook_request = pd.DataFrame(columns = ['ID','Bus','Type','P_or_Q','Direction','Quantity','Price','Time_target','Time_stamp'])
orderbook_request.set_index('ID',inplace=True)
# Create an empty dataframe to contain the accepted conditional requests
accepted_requests = pd.DataFrame(columns = ['Bus','Direction','P_or_Q','Dispatch Change','Time_target'])

#%% Function to match a new offer
matches = pd.DataFrame(columns = ['Offer','Offer Bus','Request','Request Bus','P_or_Q','Direction','Quantity','Matching Price','Time_target'])

SocialWelfare = 0
ProcurementCost = 0
for b in all_bids.index:
    new_bid = all_bids.loc[b]
    matche, orderbook_request, orderbook_offer, accepted_requests, Setpoint, flag,SocialWelfare,ProcurementCost = Market_clearing(new_bid, orderbook_request, orderbook_offer, accepted_requests, Setpoint,SocialWelfare,ProcurementCost)
    matches=matches.append(matche)
    print(b+'--'+flag)