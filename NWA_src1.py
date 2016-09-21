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
        roundpoint = 4
        test_str = str(test_int)
        test_str = "{x:.{width}f}".format(width=6,x=test_int)
        # print(test_str)
        test1 = self.S_TRAN()
        # print(str(test1))
        x1 = -0.2067
        x2 = -0.2023
        x3 = -0.2023
        y1 = -0.5059
        y2 = -0.5101
        y3 = -0.5101
        x_avg = round((x1+x2+x3)/3, roundpoint)
        y_avg = round((y1+y2+y3)/3, roundpoint)
        print(x_avg)
        print(y_avg)
        
    def S_TRAN(self):
        return {"S21":0,"S41":0,"S23":0,"S43":0}
        
