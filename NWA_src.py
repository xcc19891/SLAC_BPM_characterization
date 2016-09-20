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
        self.dat_point = 201
        self.dat_pt_str = str(self.dat_point)
        print("Welcome to SLAC BPM characterization program\n")
        myinstr = get_instruments_list()
        print("Default GPIB address for the network analyzer is \"GPIB0:16\"\n")
        while True:
            try:
                self.my_instr = instrument("GPIB0::16")
                break
            except VisaIOError:
                print("Please connect the network analyzer and try again.")
                sys.exit("Exiting program")
            
        instrument_attri = self.my_instr.ask("*IDN?")
        manufact, model_num, ser_num, firm_ver = instrument_attri.split(",",4)
        #manufact, model_num, ser_num, firm_ver, error = [0,0,0,0,0]    
        print("Instrument is a %s %s, firmware version is %s. \n" % (manufact, model_num, firm_ver))
        
        
        self.my_instr.write("OPC?;PRES") #Set instrument to preset 
        self.instrument_timeout = self.my_instr.timeout
        #print("Time out timers is %s second" %self.instrument_timeout)
        self.BPM_ser = raw_input("Please enter BPM serial number:\n--->")
        self.filedate = datetime.datetime.now()
        self.filedate_format = self.filedate.strftime("%d%b%Y")
        self.rec_time_stampe = self.filedate.strftime("%Y-%m-%d %H:%M:%S")        


        self.BPM_record = open("BPM-"+self.BPM_ser+"-cal-"+sefl.filedate_format+"_record.txt", "w+")
        self.BPM_database = open("BPM-"+self.BPM_ser+"-cal-"+sefl.filedate_format+".txt", "w+")        
        #print("Filename: %s" %self.BPM_record.name)
        #print("File mode: %s" %self.BPM_record.mode)
        self.BPM_record.write("Calibration Date:")
        self.BPM_record.write("%s\n" %self.rec_time_stampe)
        self.BPM_record.write("BPM Serial Number: %s\n" %self.BPM_ser)
        self.BPM_pmcc_str = raw_input("Please enter BPM PCMM in mm: \n--->")
        self.BPM_pmcc = (float(self.BPM_pmcc_str))*(10**-3)
        self.BPM_record.write("BPM PMCC is: %s mm\n" %self.BPM_pmcc_str)
        
        self.BPM_cnt_f = raw_input("What is the BPM's processing freq? (In MHZ)\n---> ")
        self.BPM_cnt_f_int = int(self.BPM_cnt_f)
        self.my_instr.write("CENT "+self.BPM_cnt_f+" MHZ; SPAN 0 HZ;OPC?")
        self.my_instr.write("POIN "+self.dat_pt_str)
        self.BPM_record.write("BPM processing freq: %s MHz\n" %self.BPM_cnt_f)
        self.my_instr.ask_for_values("OPC?")
        #self.my_instr.write("STAR "+self.NWA_star+" MHZ; STOP "+self.NWA_stop+" MHZ;OPC?")
        self.my_instr.write("POWE10")        
        self.my_instr.write("LINM")        
        
        print("WARNING:If you are running this process for the first time\n you need to calibrate the network analyzer")
        cal_opt = raw_input("Do you want to calibrate the Network analyzer?\n---> ")
        
        if (cal_opt == "yes") or (cal_opt == "Yes") or (cal_opt == "Y"):
            self.NWA_cal()
        else:
            self.my_instr.write("RECA1")
            print("Using cal register 1")
            print("USE AT YOUR OWN RISK!")
            
                
        self.AVER_data()
        self.center_freq=self.my_instr.ask_for_values("CENT?")
        print("Center Frequency %s. \n" % (self.center_freq))
        self.power=self.my_instr.ask_for_values("POWE?")
        print("Power at %s dBm. \n" % (self.power))

        self.S21_measure()
        self.BPM_record.close()
        self.BPM_database.close()
        
        
        

    def AVER_data(self):
        # self.instr_avgf = raw_input("What averaging factor would you like to use? (recommend 70, range 1-99)\n---->")
        self.instr_avgf = "20"
        self.instr_avgf_int = int(self.instr_avgf)
        self.my_instr.write("AVERFACT"+self.instr_avgf)
        print("Turning on averaging")
    	self.my_instr.write("AVEROON")
        self.instr_avg = self.my_instr.ask("AVERO?")
        self.instr_avg_wait_time = 5+(58)
        # print(self.instr_avg)
        if int(self.instr_avg) == 1:
        	time.sleep(0.00001)
        else:
            print ("Averaging is not turned on, something is wrong")
            
    def S_TRAN(self):
        return {"S21":0,"S41":0,"S23":0,"S43":0}
        
    def NWA_cal(self):
        self.instrument_timeout_def = self.instrument_timeout     #save the old timeout time
        self.instrument_timeout = 20.0
        self.my_instr.timeout = self.instrument_timeout        
        #Instrument calibration code
        #The 8753C Network Analyzer doesn't support the CALK35ME calkit, so the CALK35MM calkit is used
        self.my_instr.write("CALK35MM;CLES,ESE64")
        self.my_instr.write("CALIFUL2")                         #Performing a full 2-port cal
        self.my_instr.write("REFL")                             #Reflection calibration
        raw_input("Connect OPEN to port 1, then press enter")
        self.my_instr.write("CLASS11A")
        self.my_instr.ask("*OPC?")
        self.my_instr.write("DONE")
        raw_input("Connect SHORT to port 1, then press enter")
        self.my_instr.write("CLASS11B")
        self.my_instr.ask("*OPC?")
        self.my_instr.write("DONE")        
        raw_input("Connect LOAD to port 1, then press enter")
        self.my_instr.write("CLASS11C")
        self.my_instr.ask("*OPC?")
        self.my_instr.write("DONE")        
        raw_input("Connect OPEN to port 2, then press enter")
        self.my_instr.write("CLASS22A")
        self.my_instr.ask("*OPC?")
        self.my_instr.write("DONE")        
        raw_input("Connect SHORT to port 2, then press enter")
        self.my_instr.write("CLASS22B")
        self.my_instr.ask("*OPC?")
        self.my_instr.write("DONE")        
        raw_input("Connect LOAD to port 2, then press enter")
        self.my_instr.write("CLASS22C")
        self.my_instr.ask("*OPC?")
        self.my_instr.write("DONE")        
        print("Waiting for instrument to calculate calibration coefficient.")
        self.my_instr.write("REFD")

        while True:                             #Exception handling incase the calibration timesout PyVISA
            try:
                self.my_instr.ask("*OPC?")
                
                break
            except VisaIOError:
                self.my_instr.ask("*OPC?")
                
        print("Reflection calibration finished.")
        
        self.my_instr.write("TRAN")                                 #Transmission calibration
        raw_input("Connect port 1 to port 2, then press enter")
        self.my_instr.write("FWDT")
        time.sleep(1)
        print("Measuring fwd transmission")
        self.my_instr.ask("*OPC?")
        self.my_instr.write("FWDM")
        time.sleep(1)
        print("Measuring fwd match")
        self.my_instr.ask("*OPC?")
        self.my_instr.write("REVT")
        time.sleep(1)
        print("Measuring reverse transmission")
        self.my_instr.ask("*OPC?")
        self.my_instr.write("REVM")
        time.sleep(1)
        print("Measuring reverse match")
        print("waiting for instrument to calculate calibration coefficient")
        self.my_instr.ask("*OPC?")
        time.sleep(1)
        self.my_instr.write("TRAD")
        self.my_instr.ask("*OPC?")
        time.sleep(1)
        print("Transmission calibration finished")
        
        self.my_instr.write("OMII")
        time.sleep(1)
        self.my_instr.write("SAV2")
        print("Calculating calibration coefficient for the full 2-port calibration")
        while True:
            try:
                self.my_instr.ask("*OPC?")
                
                break
            except VisaIOError:
                self.my_instr.ask("*OPC?")
        print("Full 2-port calibration finished")
        self.my_instr.write("SAVE1")
        #Changing back the timeout timer
        self.instrument_timeout = self.instrument_timeout_def
        self.my_instr.timeout = self.instrument_timeout
        #print("Time out timer is changed back to %s sec" %self.my_instr.timeout)



    def S21_measure(self):
        #Change the timeout timer to work with marker output
        self.instrument_timeout_def = self.instrument_timeout     #save the old timeout time
        self.instrument_timeout = 20.0
        self.my_instr.timeout = self.instrument_timeout
        #print("Changing the timeout timer to %s sec" %self.my_instr.timeout)
        test1 = self.S_TRAN()
        test2 = self.S_TRAN()
        test3 = self.S_TRAN()        
        self.my_instr.write("FORM4")
        self.my_instr.write("WAIT")
        
        # ////////////////////////////
        # Measuring RED to BLUE
        # ////////////////////////////
        raw_input("Connect port 1 to RED and port 2 to BLUE, then press enter")
        print("Taking data\n")
        self.trace = []
        self.trace_data = []
        self.trace1 = 0.0; self.trace2 = 0.0; self.trace3 = 0.0;        
        self.my_instr.write("S21")          # S21 measurement
        self.my_instr.write("LINM")         # Linear magnitude
        # self.my_instr.write("AUTO")        
        self.my_instr.write("IFBW 100HZ")   # IF bandwidth set to 100Hz
        self.my_instr.write("AUTO")         # Auto scale
        self.my_instr.write("WAIT")         # Wait for one clean sweep
        self.my_instr.write("AVERREST")     # reset the averaging 
        self.my_instr.write("AUTO")         # Auto scale
        time.sleep(self.instr_avg_wait_time)
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace1+=i
                self.trace_data.extend([i])
        self.trace1_avg = self.trace1/self.dat_point
        print(self.trace1_avg)
        test1["S21"] = self.trace1_avg


        self.my_instr.write("AVERREST")  # reset the averaging 
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        time.sleep(self.instr_avg_wait_time)        
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace2+=i
                self.trace_data.extend([i])
        self.trace2_avg = self.trace2/self.dat_point
        print(self.trace2_avg)        
        test2["S21"] = self.trace2_avg


        self.my_instr.write("AVERREST")  # reset the averaging 
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        time.sleep(self.instr_avg_wait_time)         
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace3+=i
                self.trace_data.extend([i])
        self.trace3_avg = self.trace3/self.dat_point
        print(self.trace3_avg)        
        test3["S21"] = self.trace3_avg
        print("\n\n")        

        # ////////////////////////////
        # Measuring RED to GREEN
        # ////////////////////////////            
        raw_input("Connect port 1 to RED and port 2 to GREEN, then press enter")
        print("Taking data\n")
        self.trace = []
        self.trace_data = []
        self.trace1 = 0.0; self.trace2 = 0.0; self.trace3 = 0.0;
        self.my_instr.write("AVERREST")  # reset the averaging 
        self.my_instr.write("AUTO")
        self.my_instr.write("WAIT")
        time.sleep(self.instr_avg_wait_time) 
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace1+=i
                self.trace_data.extend([i])
        self.trace1_avg = self.trace1/self.dat_point
        print(self.trace1_avg)
        test1["S41"] = self.trace1_avg


        self.my_instr.write("AVERREST")  # reset the averaging 
        time.sleep(self.instr_avg_wait_time) 
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace2+=i
                self.trace_data.extend([i])
        self.trace2_avg = self.trace2/self.dat_point
        print(self.trace2_avg)        
        test2["S41"] = self.trace2_avg
        

        self.my_instr.write("AVERREST")  # reset the averaging 
        time.sleep(self.instr_avg_wait_time) 
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace3+=i
                self.trace_data.extend([i])
        self.trace3_avg = self.trace3/self.dat_point
        print(self.trace3_avg)        
        test3["S41"] = self.trace3_avg
        print("\n\n")
        
        # ////////////////////////////
        # Measuring YELLOW to GREEN
        # ////////////////////////////        
        raw_input("Connect port 1 to YELLOW and port 2 to GREEN, then press enter")
        print("Taking data\n")
        self.trace = []
        self.trace_data = []
        self.trace1 = 0.0; self.trace2 = 0.0; self.trace3 = 0.0;
        self.my_instr.write("AUTO")
        self.my_instr.write("WAIT")
        
        self.my_instr.write("AVERREST")  # reset the averaging 
        self.my_instr.write("AUTO")        
        time.sleep(self.instr_avg_wait_time)
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace1+=i
                self.trace_data.extend([i])
        self.trace1_avg = self.trace1/self.dat_point
        print(self.trace1_avg)
        test1["S43"] = self.trace1_avg


        self.my_instr.write("AVERREST")  # reset the averaging 
        time.sleep(self.instr_avg_wait_time) 
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace2+=i
                self.trace_data.extend([i])
        self.trace2_avg = self.trace2/self.dat_point
        print(self.trace2_avg)        
        test2["S43"] = self.trace2_avg
        

        self.my_instr.write("AVERREST")  # reset the averaging 
        time.sleep(self.instr_avg_wait_time) 
        self.my_instr.write("WAIT")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace3+=i
                self.trace_data.extend([i])
        self.trace3_avg = self.trace3/self.dat_point
        print(self.trace3_avg)        
        test3["S43"] = self.trace3_avg
        print("\n\n")

        # ////////////////////////////
        # Measuring YELLOW to BLUE
        # ////////////////////////////        
        raw_input("Connect port 1 to YELLOW and port 2 to BLUE, then press enter")
        print("Taking data\n")
        self.trace = []
        self.trace_data = []
        self.trace1 = 0.0; self.trace2 = 0.0; self.trace3 = 0.0;

        self.my_instr.write("AUTO")
        self.my_instr.write("AVERREST")  # reset the averaging 
        self.my_instr.write("AUTO")        
        time.sleep(self.instr_avg_wait_time)
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace1+=i
                self.trace_data.extend([i])
        self.trace1_avg = self.trace1/self.dat_point
        print(self.trace1_avg)
        test1["S23"] = self.trace1_avg


        self.my_instr.write("AVERREST")  # reset the averaging 
        time.sleep(self.instr_avg_wait_time) 
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace2+=i
                self.trace_data.extend([i])
        self.trace2_avg = self.trace2/self.dat_point
        print(self.trace2_avg)        
        test2["S23"] = self.trace2_avg
        

        self.my_instr.write("AVERREST")  # reset the averaging 
        time.sleep(self.instr_avg_wait_time) 
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace3+=i
                self.trace_data.extend([i])
        self.trace3_avg = self.trace3/self.dat_point
        print(self.trace3_avg)        
        test3["S23"] = self.trace3_avg
        print("\n\n")      
        
        #Changing back the timeout timer
        self.instrument_timeout = self.instrument_timeout_def
        self.my_instr.timeout = self.instrument_timeout
        #print("Time out timer is changed back to %s sec" %self.my_instr.timeout)
        mm_conv = (10**3)

        x1 = self.BPM_pmcc*((test1["S41"]-test1["S21"])+(test1["S43"]-test1["S23"]))/(test1["S21"]+test1["S41"]+test1["S43"]+test1["S23"])
        y1 = self.BPM_pmcc*((test1["S41"]-test1["S43"])+(test1["S21"]-test1["S23"]))/(test1["S21"]+test1["S41"]+test1["S43"]+test1["S23"])
        
        x2 = self.BPM_pmcc*((test2["S41"]-test2["S21"])+(test2["S43"]-test2["S23"]))/(test2["S21"]+test2["S41"]+test2["S43"]+test2["S23"])
        y2 = self.BPM_pmcc*((test2["S41"]-test2["S43"])+(test2["S21"]-test2["S23"]))/(test2["S21"]+test2["S41"]+test2["S43"]+test2["S23"])
        
        x3 = self.BPM_pmcc*((test3["S41"]-test3["S21"])+(test3["S43"]-test3["S23"]))/(test3["S21"]+test3["S41"]+test3["S43"]+test3["S23"])
        y3 = self.BPM_pmcc*((test3["S41"]-test3["S43"])+(test3["S21"]-test3["S23"]))/(test3["S21"]+test3["S41"]+test3["S43"]+test3["S23"])
                
        x_avg = (x1+x2+x3)/3
        y_avg = (y1+y2+y3)/3

        print("First sets of sample data:\n %s" %test1)
        print("Second sets of sample data:\n %s" %test2)
        print("Third sets of sample data:\n %s" %test3)
        print("X center(mm) for\n1st set: %s,\n2nd set: %s,\n3rd set: %s\n" %((x1*mm_conv),(x2*mm_conv),(x3*mm_conv)))
        print("Y center(mm) for\n1st set: %s,\n2nd set: %s,\n3rd set: %s\n" %((y1*mm_conv),(y2*mm_conv),(y3*mm_conv)))
        print("X average center(mm) is at: %s\n" % x_avg)
        print("Y average center(mm) is at: %s\n" % y_avg)
  
        self.BPM_record.write("Record format is: \n")
        self.BPM_record.write("S21,S41,S23,S43\n")
        self.BPM_record.write("%s\n" %test1)
        self.BPM_record.write("%s\n" %test2)
        self.BPM_record.write("%s\n" %test2)
        self.BPM_record.write("X center(mm) is at:\n")
        self.BPM_record.write("%s,%s,%s\n" %((x1*mm_conv),(x2*mm_conv),(x3*mm_conv)))
        self.BPM_record.write("Y center(mm) is at:\n")
        self.BPM_record.write("%s,%s,%s\n" %((y1*mm_conv),(y2*mm_conv),(y3*mm_conv)))
        
        self.BPM_record.write("X average center(mm) is at: %s\n" % x_avg)
        self.BPM_record.write("Y average center(mm) is at: %s\n" % y_avg)

            