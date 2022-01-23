# -*- coding: utf-8 -*-
"""
Created on Mon Jan 18 22:09:55 2021

@author: Rahul N
"""

import pandas as pd
import numpy as np

def LinDistFlow_check(SetpointGP, SetpointGQ,Quantity,offer_bus,request_bus,direction,new_offer_PQ):
    
    epsilon=0.00001 # Tolerance                    
    lines_data = pd.read_excel(open('Data_Files/network15bus.xlsx', 'rb'),sheet_name='Branch',index_col=0)
    lines = list(lines_data.index)  # index for lines
    lines_data.columns = ['From','To','R','X','Lim']
    bus_data = pd.read_excel(open('Data_Files/network15bus.xlsx', 'rb'),sheet_name='Bus',index_col=0)
    bus_data.columns = ['type', 'Vmax', 'Vmin']
    nodes = list(bus_data.index)    # index for nodes
    Vmax=bus_data['Vmax'].to_numpy()
    Vmin=bus_data['Vmin'].to_numpy()
                        
    no_of_nodes=len(nodes)
    no_of_lines=len(lines)

    #%% Generating Incident matrix
    IM_pd = pd.DataFrame(np.zeros((no_of_lines,no_of_nodes)), columns=nodes, index=lines)
    r=np.zeros((no_of_lines,1))
    x=np.zeros((no_of_lines,1))
    i=0

    for l in lines:
        IM_pd[lines_data.loc[l,'From']][l]=1
        IM_pd[lines_data.loc[l,'To']][l]=-1
        r[i] = lines_data.loc[l,'R']
        x[i] = lines_data.loc[l,'X']
        i+=1
        
    IM = IM_pd.to_numpy()
    
    #%% Line capacity
    LC_pd = pd.DataFrame(np.zeros((1,no_of_lines)), columns=lines)
    for l in lines:
        LC_pd[l]=lines_data.loc[l,'Lim']

    Line_Cap = LC_pd.to_numpy()
    
    #%% Getting load at each node
    P_pd=pd.DataFrame(np.zeros((1,no_of_nodes)), columns=nodes)
    Q_pd=pd.DataFrame(np.zeros((1,no_of_nodes)), columns=nodes)

    i=0
    for n in nodes:
        P_pd[n]=SetpointGP[i]
        Q_pd[n]=SetpointGQ[i]
        i+=1
        
    if direction == 'Up':
        k = nodes[offer_bus]
        m = nodes[request_bus]
    if direction == 'Down':
        m = nodes[offer_bus]
        k = nodes[request_bus]
    
    congestion =True
    while congestion:
        if new_offer_PQ == 'P':
            P_pd[k]=P_pd[k]+Quantity
            P_pd[m]=P_pd[m]-Quantity
        elif new_offer_PQ == 'Q':
            Q_pd[k]=Q_pd[k]+Quantity
            Q_pd[m]=Q_pd[m]-Quantity
        P=np.zeros((1,15))
        P=P_pd.to_numpy()
        
        Q=np.zeros((1,15))
        Q=Q_pd.to_numpy()    
        
        A=np.delete(np.transpose(IM),1,0)
        Bp=np.delete(np.transpose(P),1,0)
        Line_P= np.linalg.solve(A,Bp)
        Bq=np.delete(np.transpose(Q),1,0)
        Line_Q= np.linalg.solve(A,Bq)

        Line_S=np.sqrt(np.square(Line_P) + np.square(Line_Q))
        
        #%% Finding Voltage 
        
        Av=np.append(np.zeros((1,no_of_nodes)),IM , axis=0)
        Av[0][0]=1
        Bv=np.append(1,2*(np.multiply(r,Line_P)+np.multiply(x,Line_Q)))
        Node_V= np.linalg.solve(Av,Bv)

        if (np.greater_equal(Line_Cap,np.transpose(Line_P)).all() == True) and (np.greater_equal(Line_Cap,-np.transpose(Line_P)).all() == True) and (np.greater_equal(Vmax,Node_V).all() == True) and (np.greater_equal(Node_V,Vmin).all() == True):
            congestion =False
            #print("Done")
        else:
            if new_offer_PQ == 'P':
                P_pd[k]=P_pd[k]-Quantity
                P_pd[m]=P_pd[m]+Quantity 
            elif new_offer_PQ == 'Q':
                Q_pd[k]=Q_pd[k]-Quantity
                Q_pd[m]=Q_pd[m]+Quantity
            Quantity=Quantity-epsilon
            if (Quantity <= 0):
                Quantity=0
                congestion =False    
    return Quantity
    
