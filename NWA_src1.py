'''
SLAC National Accelerator Laboratory
Instrumentation and Controls Division
Date: 03/14/2013
author: Chengcheng Xu
Summary:
Automate the BPM characterization process by using PyVISA to communicate with a HP8753C Network Analyzer.  
'''
from visa import *
from math import pow, exp
import time
import sys
import datetime

class BPM_chara:
    def __init__(self):
        test_int = 0.103500000
        roundpoint = 5
        test_str = str(test_int)
        test_str = "{x:.{width}f}".format(width=6,x=test_int)
        # print(test_str)
        test1 = self.S_TRAN()
        print(str(test1))
        
    def S_TRAN(self):
        return {"S21":0,"S41":0,"S23":0,"S43":0}
        
