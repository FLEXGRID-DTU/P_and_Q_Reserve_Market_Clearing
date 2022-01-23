# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 13:33:39 2021

@author: rahul
"""
import pandas as pd
from Matching_Algorithm import matching

def Market_clearing(new_bid, orderbook_request, orderbook_offer, accepted_requests, Setpoint,SocialWelfare,ProcurementCost):
    
    matches = pd.DataFrame(columns = ['Offer','Offer Bus','Request','Request Bus','P_or_Q','Direction','Quantity','Matching Price','Time_target'])

    Setpoint, status, orderbook_request, orderbook_offer, accepted_requests, matches, flag ,SocialWelfare, ProcurementCost = matching('new', Setpoint, new_bid, orderbook_request, orderbook_offer, accepted_requests, matches,SocialWelfare,ProcurementCost)
    
    # If there was at least a match with an unconditional request, try again on older bids
    if status == 'match' and not orderbook_offer[(orderbook_offer.Direction == new_bid.at['Direction']) & (orderbook_offer.Time_target == new_bid.at['Time_target'])].empty:
        general_status = 'match'
        while general_status == 'match': # As long as previous offers are matching with unconditional requests, check for matches
            general_status = 'no match'
            for O in orderbook_offer.index:
                old_offer = orderbook_offer.loc[O].copy()
                if old_offer['Time_target'] == new_bid.at['Time_target']:
                    Setpoint, status, orderbook_request, orderbook_offer, accepted_requests, matches, flag_tp, SocialWelfare,ProcurementCost = matching('old',Setpoint, old_offer, orderbook_request, orderbook_offer, accepted_requests, matches,SocialWelfare,ProcurementCost)
                    if status == 'match':
                        general_status = 'match'
    return matches, orderbook_request, orderbook_offer, accepted_requests, Setpoint, flag ,SocialWelfare,ProcurementCost
