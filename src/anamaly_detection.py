#!C:/Program Files/Python36/python.exe

# #####################################################################################
# Author : Raghu Patibandla
# Date   : July 5th 2017
# ====================================================================================
# Program to build network and purchase history,  and performing anamaly detection
# ====================================================================================
# Inputs parameters: None
# However, two json files are expected 
# log_input/batch_log.json  : consumed for building network and purchase history
# log_input/stream_log.json : processed for anamaly detection and updates
#
# output : log_output/flagged_purchases.json - all the anamalies are noted in this file
# 
# Assumption:  batch_log should be used just to build the network and purchase history
#              Anamaly detection process is not performed on this.
#
# Libraries needed:  All the libraries needed for this program are listed with imports
#                 :  networkx needs to be installed - used for building network graph
#
# Example :  How to run on Windows OS
# C:\>python src/anamaly_detection.py 
# ====================================================================================
# Please Note: In the given run.sh, the parameters sequence-
#	feature 3 output(hours.txt) before the feature 2 output (resources.txt)
#
# #####################################################################################

#@profile
import json
import math
import datetime
from collections import defaultdict

# Network builder
import networkx as nx
#import matplotlib.pyplot as plt
G=nx.Graph()

# Dictionary to keep the flexible parameters D and T
flexi_params = dict()

# Dictionary to keep all users' purchase history - This is going to be a dict of dicts
all_users_purch_hist = defaultdict(dict)


# main function
def main_func():
    # globalizing the variables
    global G, flexi_params, all_users_purch_hist

    # List to keep the lines that identified in anamaly detection process
    ad_lines = []

    # Configurable items
    # ------------------

    # input json file name
    feature_build_input = "log_input/batch_log.json"

    # input json file name
    feature_ad_input = "log_input/stream_log.json"

    # Output file name
    feature_output = "log_output/flagged_purchases.json"

    # build json process starts
    with open(feature_build_input, "r") as json_file:
        for line in json_file :
            if (not (len(line.strip()) == 0 ))  :

                json_line = json.loads(line)
                if ('D' in json_line.keys()) :          # Get flexible parameters D and T
                    flexi_params = json_line
                    continue
                else :                                  # json data line
                    # build/update network
                    if (json_line['event_type'] in ['befriend','unfriend']) :
                        build_network_func(json_line['id1'], json_line['id2'], json_line['event_type'])

                    # dealing with purchase transaction
                    elif (json_line['event_type'] == 'purchase') :
                        # build/update purchase hisotry
                        build_purchase_hist_func(json_line['id'], json_line['timestamp'], json_line['amount'])

            else :                                      # blank line
                continue
        # End of for loop

    # stream json process starts
    with open(feature_ad_input, "r") as json_file:
        for line in json_file :
            if (not (len(line.strip()) == 0 ))  :

                json_line = json.loads(line)
                # build/update network
                if (json_line['event_type'] in ['befriend','unfriend']) :
                    build_network_func(json_line['id1'], json_line['id2'], json_line['event_type'])

                # dealing with purchase transaction
                elif (json_line['event_type'] == 'purchase') :
                    # build/update purchase hisotry
                    build_purchase_hist_func(json_line['id'], json_line['timestamp'], json_line['amount'])

                    #  ***** anamaly detection process start here *****
                    #  ================================================
                    # 1. Get network of the current user until given depth (D)
                    frnds_of_user = get_network(json_line['id'])

                    # 2. Get network's purchase history
                    nw_purch_hist = dict()
                    if (frnds_of_user is not None) :
                        nw_purch_hist = get_purch_hist(frnds_of_user)

                    # 3. Get amounts and sd of them
                    ad_proc_amounts = list(nw_purch_hist.values())
                    ad_proc_amounts = list(map(float, ad_proc_amounts))

                    if (len(ad_proc_amounts) > 0) :
                        ad_proc_mean = get_mean(ad_proc_amounts)
                        ad_proc_sd = get_sd(ad_proc_amounts)

                        # 4. Check if current amount is a anamaly
                        if (float(json_line['amount']) > ( ad_proc_mean + (3*ad_proc_sd))) :
                            ad_lines.append(line)
            else :                                      # blank line
                continue
        # End of for loop

        # Writing anamalies
        with open(feature_output, 'w') as f:
            for l in ad_lines :
                f.write('%s' % (l))



    return None

# function to build/update network 
def build_network_func(id1, id2, event_type):
    if (event_type == 'befriend') :    # setting friend bi-drectional edges
        G.add_edge(id1,id2)
    elif (event_type == 'unfriend') :  # ending an edge
        G.remove_edge(id1,id2)
    return None

# function to build purchase history
def build_purchase_hist_func(id, ts, amt):
    # Adding purchase history for the user
    all_users_purch_hist[id][ts] = amt

    # Keeping only "T" number of transactions in the history 
    if (len(all_users_purch_hist[id]) >= int(flexi_params['T'])) :
        old_ts_key = list(all_users_purch_hist[id].keys()).pop(0)   # Get older key
        del all_users_purch_hist[id][old_ts_key]       # Remove older transaction
    return None

# function to calculate mean of given amounts
def get_mean(amounts) :
    mean_amts = float()
    mean_amts = round(sum(amounts)/len(amounts), 2)
    return  mean_amts   

# function to calculate standard deviation of given amounts
def get_sd(amounts) :
    mean_amts = get_mean(amounts)
    residuals_squared =  list(map(lambda d: (d-mean_amts)**2, amounts))
    sd = round(math.sqrt(sum(residuals_squared)/len(amounts)),2)
    return sd

# function to get friends network until given depth (D)
def get_network(userId) :
    if (G.has_node(userId)) :
        path=nx.single_source_shortest_path(G,userId, int(flexi_params['D']))
        friends_network = list(path.keys())
        return friends_network
    else : return None

# function to get "T" number of purchase history of network
def get_purch_hist(network) :
    # Dictionary to keep network's purch history
    network_purch_hist = dict()
    # Dictionary to keep temp. purchase history as part of anamaly detection process
    ad_network_purch_hist = dict()

    for frnd in network :
        network_purch_hist.update(all_users_purch_hist[frnd])

    # sort on timestamp
    # key_list list is used for multiple purposes 1. to store all network timestamps
    key_list = network_purch_hist.keys()

    # convetng to timestamp
    key_ts_list = list(map(lambda d: datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S'), key_list))
    key_ts_list.sort()

    # Repurposing the key_list to store sorted keys
    key_list=[]
    key_list = list(map(lambda d: str(d), key_ts_list[-int(flexi_params['T']):]))
   
    # putting together the limited purchsase history
    for k in key_list :
        ad_network_purch_hist[k] = network_purch_hist[k]

    return ad_network_purch_hist



if __name__ == '__main__':
    main_func()


