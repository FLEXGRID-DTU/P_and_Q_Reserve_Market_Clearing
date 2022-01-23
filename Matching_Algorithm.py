# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 14:22:37 2021

@author: rahul
"""
import pandas as pd
from itertools import combinations
from operator import add
from LinDistFlow_check import LinDistFlow_check

bus = pd.read_excel(open('Data_Files/network15bus.xlsx', 'rb'),sheet_name='Bus',index_col=0)
bus.columns = ['type', 'Vmax', 'Vmin']
nodes = list(bus.index)

def matching(bid_type, Setpoint, bid, orderbook_request, orderbook_offer, accepted_requests, matches, SocialWelfare,ProcurementCost):
    
    #bid_type: new or old
    
    epsilon = 0.00001 # Tolerance
    status = 'no match' # Marker to identify if there was a match with unconditional requests or not (if so, the order book should be checked for new matches)
    flag = 'NaN' # initialize the output flag 
    
    time_target = bid.at['Time_target']
    Setpoint_P = Setpoint.at[time_target,'Setpoint_P']
    Setpoint_Q = Setpoint.at[time_target,'Setpoint_Q']
    direction = bid.at['Direction']
    P_or_Q = bid.at['P_or_Q']
    if bid_type == 'new':
        bid_nature = bid.at['Bid'] # Offer or request
    elif bid_type == 'old':
        bid_nature = 'Offer'
    
    if bid_nature == 'Offer':
        offer_bus = nodes.index(bid.at['Bus'])
        offer_price = bid.at['Price']
        offer_quantity = bid.at['Quantity']
        offer_index = bid.name
        offer_time_stamp = bid.at['Time_stamp']

        
        # Make sure that there are requests left to be matched
        if orderbook_request[(orderbook_request.P_or_Q == P_or_Q) & (orderbook_request.Direction == direction) & (orderbook_request.Time_target == time_target)].empty:
            flag = 'Empty orderbook'
            orderbook_offer.loc[offer_index]=[nodes[offer_bus],P_or_Q,direction,offer_quantity,offer_price,time_target,offer_time_stamp]
            orderbook_offer.sort_values(by=['Time_target','Price','Time_stamp'], ascending=[True,True,True], inplace=True) # Sort by price and by time submission and gather by time target
            return Setpoint, status, orderbook_request, orderbook_offer, accepted_requests, matches, flag, SocialWelfare,ProcurementCost
        
        # Else, list of requests to look into
        orderbook = orderbook_request
        
    elif bid_nature == 'Request':
        request_bus = nodes.index(bid.at['Bus'])
        request_price = bid.at['Price']
        request_quantity = bid.at['Quantity']
        request_index = bid.name
        request_type = bid.at['Type']
        request_time_stamp = bid.at['Time_stamp']
        
        # Make sure that there are offers left to be matched
        if orderbook_offer[(orderbook_offer.P_or_Q == P_or_Q) & (orderbook_offer.Direction == direction) & (orderbook_offer.Time_target == time_target)].empty:
            flag = 'Empty orderbook'
            orderbook_request.loc[request_index]=[nodes[request_bus],request_type,P_or_Q,direction,request_quantity,request_price,time_target,request_time_stamp]
            orderbook_request.sort_values(by=['Time_target','Price','Time_stamp'], ascending=[True,False,True], inplace=True) # Sort by price and by time submission and gather by time target
            return Setpoint, status, orderbook_request, orderbook_offer, accepted_requests, matches, flag, SocialWelfare,ProcurementCost
        
        # Else, list of requests to look into
        orderbook = orderbook_offer

# Check matching with all the requests (in the same direction)
    for ID in orderbook.index:
        
        if orderbook.at[ID,'P_or_Q'] == P_or_Q and orderbook.at[ID,'Direction'] == direction and orderbook.at[ID,'Time_target'] == time_target:
            if bid_nature == 'Offer':
                request_price = orderbook_request.at[ID,'Price']
                request_index = ID
                
            elif bid_nature == 'Request':
                offer_price = orderbook_offer.at[ID,'Price']
                offer_index = ID
            
            # Make sure that the prices are matching
            if offer_price <= request_price:
                
                if bid_nature == 'Offer':
                    request_bus = nodes.index(orderbook_request.at[ID,'Bus'])
                    Offered = offer_quantity
                    Requested = orderbook_request.at[ID,'Quantity']
                    request_type = orderbook_request.at[ID,'Type']
                    request_time_stamp = orderbook_request.at[ID,'Time_stamp']
                elif bid_nature == 'Request':
                    offer_bus = nodes.index(orderbook_offer.at[ID,'Bus'])
                    Offered = orderbook_offer.at[ID,'Quantity']
                    Requested = request_quantity
                    offer_time_stamp = orderbook_offer.at[ID,'Time_stamp']
                    
                Quantity = min(Offered,Requested) # Initially, the maximum quantity that can be exchanged is the minimum of the quantities of the bids
                # Check for this match only
                Quantity = LinDistFlow_check(Setpoint_P,Setpoint_Q,Quantity,offer_bus,request_bus,direction,P_or_Q)

                # If this match alone is feasible, check all combinations with previously accepted conditional requests
                if Quantity > epsilon and not accepted_requests.empty:
                    # Create all combinations
                    cond_requests = []
                    for i in list(accepted_requests.index):
                        if accepted_requests.at[i,'Time_target'] == time_target and accepted_requests.at[i,'P_or_Q'] == P_or_Q:
                            cond_requests.append(i) # List of accepted conditional requests, identified by their index in the dataframe
                    comb=[] # List for all combinations of accepted conditional requests with the request under evaluation
                    # Code to create all combinations
                    for i in range(len(cond_requests)):
                        new_comb = [list(l) for l in combinations(cond_requests,i+1)]
                        for n in new_comb:
                            comb.append(n)
                            
                    # Remove combinations for up and down regulation at the same bus
                    for cr in range(len(cond_requests)-1):
                        first = cond_requests[cr]
                        second = cond_requests[cr+1]
                        if accepted_requests.at[first,'Bus'] == accepted_requests.at[second,'Bus'] and accepted_requests.at[first,'Direction'] != accepted_requests.at[second,'Direction']:
                            for c in comb:
                                if first in c and second in c:
                                    comb.remove(c)
                    
                    # PTDF check for all combinations
                    for c in comb:
                        if Quantity > epsilon: # If the quantity is still above zero
                            if P_or_Q == 'P':
                                Setpoint_new = Setpoint_P
                                for i in c:
                                    Setpoint_new = list(map(add,accepted_requests.at[i,'Dispatch Change'],Setpoint_new))
                                Quantity = LinDistFlow_check(Setpoint_new,Setpoint_Q,Quantity,offer_bus,request_bus,direction,P_or_Q)
                            elif P_or_Q == 'Q':
                                Setpoint_new = Setpoint_Q
                                for i in c: # Update the Setpoint with all the corresponding requests and matching offers
                                    Setpoint_new = list(map(add,accepted_requests.at[i,'Dispatch Change'],Setpoint_new))
                                Quantity = LinDistFlow_check(Setpoint_P,Setpoint_new,Quantity,offer_bus,request_bus,direction,P_or_Q)
                        else: # If the quantity is less than zero, the calculation can stop for this request: the match is unfeasible
                            break
                
                if Quantity > epsilon: # Line constraints are respected
                    flag = 'Match'
                    # The older bid sets the price
                    SocialWelfare = SocialWelfare + Quantity*(request_price-offer_price)
                    if request_time_stamp > offer_time_stamp:
                        matching_price = request_price
                    elif request_time_stamp < offer_time_stamp:
                        matching_price = offer_price
                    matches = matches.append({'Offer':offer_index,'Offer Bus':nodes[offer_bus],'Request':request_index,'Request Bus':nodes[request_bus],'P_or_Q':P_or_Q, 'Matching Price':matching_price,'Direction':direction,'Quantity':Quantity, 'Time_target':time_target},ignore_index=True)
                    ProcurementCost = ProcurementCost + Quantity*matching_price
                    # Calculate the corresponding changes in the Setpoint
                    Delta = [0] * len(Setpoint_P)
                    if direction == 'Up':
                        Delta[offer_bus]+=Quantity
                        Delta[request_bus]-=Quantity
                    elif direction == 'Down':
                        Delta[offer_bus]-=Quantity
                        Delta[request_bus]+=Quantity
                        
                    # If the accepted request is unconditional, modify the Setpoint and update the status marker
                    if request_type == 'Unconditional':
                        if P_or_Q == 'P':
                            Setpoint.at[time_target,'Setpoint_P'] = list(map(add,Setpoint_P,Delta))
                        elif P_or_Q == 'Q':
                            Setpoint.at[time_target,'Setpoint_Q'] = list(map(add,Setpoint_Q,Delta))
                        status = 'match'
                        
                    elif request_type == 'Conditional':
                        # Check if request is already in the dataframe of accepted requests
                        if request_index in accepted_requests.index:
                            # If so, update the corresponding dispatch change to inlcude the new offer
                            Delta_init = accepted_requests.at[request_index,'Dispatch Change']
                            Delta_init = list(map(add,Delta_init,Delta))
                            accepted_requests.at[request_index,'Dispatch Change'] = Delta_init
                        # If not, create a new entry in the dataframe
                        else:
                            accepted_requests.loc[request_index]=[nodes[request_bus], direction, P_or_Q, Delta, time_target]
                            accepted_requests.sort_values(by=['Bus'], inplace=True) # Reorganize to group requests per node for the elimination of combinations with up and down requests at the same bus
                    
                    # Update quantities of these offer and request
                    if bid_nature == 'Offer':
                        offer_quantity = Offered - Quantity
                        orderbook_request.at[ID,'Quantity'] = Requested - Quantity
                        if orderbook_request.at[ID,'Quantity'] < epsilon: # If the request was completely matched
                            orderbook_request = orderbook_request.drop([ID], axis=0)

                        if offer_quantity < epsilon: # If the offer was completely matched
                            if bid_type == 'old': # In the case of checking the bids in the order book, the corresponding row must be dropped
                                orderbook_offer = orderbook_offer.drop([offer_index], axis=0)
                            return Setpoint, status, orderbook_request, orderbook_offer, accepted_requests, matches, flag, SocialWelfare, ProcurementCost
                        
                    elif bid_nature == 'Request':
                        request_quantity = Requested - Quantity
                        orderbook_offer.at[ID,'Quantity'] = Offered - Quantity
                        if orderbook_offer.at[ID,'Quantity'] < epsilon: # If the offer was completely matched
                            orderbook_offer = orderbook_offer.drop([ID], axis=0)

                        if request_quantity < epsilon: # If the offer was completely matched
                            return Setpoint, status, orderbook_request, orderbook_offer, accepted_requests, matches, flag, SocialWelfare, ProcurementCost
                else:
                    flag = 'No match (congestions)'
            else:
                flag = 'No match (price)'
                break
            
    if bid_nature == 'Offer':
        if offer_quantity > epsilon: # If the offer was not completely matched after trying all requests, update and order the book
            orderbook_offer.loc[offer_index]=[nodes[offer_bus],P_or_Q,direction,offer_quantity,offer_price,time_target,offer_time_stamp]
            orderbook_offer.sort_values(by=['Time_target','Price','Time_stamp'], ascending=[True,True,True], inplace=True) # Sort by price and by time submission and gather by time target
    elif bid_nature == 'Request':
        if request_quantity > epsilon: # If the request was not completely matched after trying all offers, update and order the book
            orderbook_request.loc[request_index]=[nodes[request_bus],request_type,P_or_Q, direction,request_quantity,request_price,time_target,request_time_stamp]
            orderbook_request.sort_values(by=['Time_target','Price','Time_stamp'], ascending=[True,False,True], inplace=True) # Sort by price and by time submission and gather by time target

    return Setpoint, status, orderbook_request, orderbook_offer, accepted_requests, matches, flag, SocialWelfare, ProcurementCost
