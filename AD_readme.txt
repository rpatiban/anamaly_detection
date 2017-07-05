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
# Please Note: For handing huge inputs - splitting and multiprocessing needs to be
# implemented.  Although I wanted to implement the multiprocessing - in the given time
# personal commitments did not allow me to include that feature.
# #####################################################################################
