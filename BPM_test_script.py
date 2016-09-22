'''
SLAC National Accelerator Laboratory
Instrumentation and Controls Division
Date: 03/18/2013
author: Chengcheng Xu
'''
from NWA_src1 import *
i = 1
while i == 1:
	BPM = BPM_chara()
	redo_opt = raw_input("Would you like to characterize another BPM?\n---> ")
	if (redo_opt == "YES") or (redo_opt == "YEs") or (redo_opt == "Yes") or (redo_opt == "yes") or (redo_opt == "Y") or (redo_opt == "y"):
		i = 1
	else:
		i = 0