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
        self.dat_point = 201    # Setting the NWA data point
        self.roundpoint = 4
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
            
        instrument_attri = self.my_instr.ask("*IDN?")    # Getting the instrument information
        manufact, model_num, ser_num, firm_ver = instrument_attri.split(",",4)
        #manufact, model_num, ser_num, firm_ver, error = [0,0,0,0,0]    
        print("Instrument is a %s %s, firmware version is %s. \n" % (manufact, model_num, firm_ver))
        
        
        self.my_instr.write("OPC?;PRES")    # Set instrument to preset 
        self.instrument_timeout = self.my_instr.timeout
        #print("Time out timers is %s second" %self.instrument_timeout)
        self.BPM_ser = raw_input("Please enter BPM serial number:\n--->")

        self.filedate = datetime.datetime.now()    # Getting time of characterization
        self.filedate_format = self.filedate.strftime("%d%b%Y-%H_%M_%S")
        self.rec_time_stampe = self.filedate.strftime("%Y-%m-%d %H:%M:%S")
        # Opening files for recording
        self.BPM_record = open("BPM-"+self.BPM_ser+"-cal-"+self.filedate_format+".txt", "w+")
        
        self.BPM_record.write("Calibration Date:")
        self.BPM_record.write("%s\n" %self.rec_time_stampe)
        self.BPM_record.write("BPM Serial Number: %s\n" %self.BPM_ser)
        self.BPM_pmcc_str = raw_input("Please enter BPM PCMM in mm (1/4 of the BPM inner diameter): \n--->")
        self.BPM_pmcc = (float(self.BPM_pmcc_str))
        self.BPM_record.write("BPM PCMM: %s mm (1/4 of the inner diameter)\n" %self.BPM_pmcc_str)
        self.BPM_cnt_f = raw_input("What is the BPM's processing freq? (In MHZ)\n---> ")
        self.BPM_cnt_f_int = int(self.BPM_cnt_f)    # Setting NWA frequency
        self.my_instr.write("CENT "+self.BPM_cnt_f+" MHZ; SPAN 0 HZ;OPC?")    # Changing the span to 0Hz because we are only interested in one freq.
        self.my_instr.write("POIN "+self.dat_pt_str)    # Set data point
        self.BPM_record.write("BPM processing freq: %s MHz\n" %self.BPM_cnt_f)
        self.my_instr.ask_for_values("OPC?")
        #self.my_instr.write("STAR "+self.NWA_star+" MHZ; STOP "+self.NWA_stop+" MHZ;OPC?")
        self.my_instr.write("POWE10")    # For the HP8753D model it can only output stimulis power of 10dBm
        self.my_instr.write("LINM")      # Setting display to linear magnitude  
        
        print("WARNING:If you are running this process for the first time\n you need to calibrate the network analyzer")
        cal_opt = raw_input("Do you want to calibrate the Network analyzer?\n---> ")
        if (cal_opt == "yes") or (cal_opt == "Yes") or (cal_opt == "Y"):
            self.NWA_cal()
        else:
            self.my_instr.write("RECA1")
            print("Using cal register 1")
            print("USE AT YOUR OWN RISK!")
                        
        self.AVER_data()    # Turning on averaging 
        self.center_freq=self.my_instr.ask_for_values("CENT?")
        freq1 = str(self.center_freq).split('[')[1]
        self.center_freq = freq1.split(']')[0]
        print("Center Frequency: %s Hz\n" % (self.center_freq))    # Double checking the center freq
        self.power=self.my_instr.ask_for_values("POWE?")
        print("Power at %s dBm. \n" % (self.power))              # Double checking the stimulis power
        self.BPM_record.write("NWA stimulis power: %s dBm\n" %self.power)

        self.S21_measure()
        self.BPM_record.close()
                
        

    def AVER_data(self):
        # self.instr_avgf = raw_input("What averaging factor would you like to use? (recommend 70, range 1-99)\n---->")
        self.instr_avgf = "20"
        self.instr_avgf_int = int(self.instr_avgf)
        self.my_instr.write("AVERFACT"+self.instr_avgf)
        print("Turning on averaging")
    	self.my_instr.write("AVEROON")
        self.instr_avg = self.my_instr.ask("AVERO?")
        # self.instr_avg_wait_time = 5+(58)    # Guess work on hosw long to wait for the averaging to be done
        self.instr_avg_wait_time = 2         # For testing only
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
        test1_str = self.S_TRAN()
        test2_str = self.S_TRAN()
        test3_str = self.S_TRAN()    
        self.my_instr.write("FORM4")    # Output in ASCII 
        self.my_instr.write("WAIT")
        
        # ////////////////////////////
        # Measuring RED to BLUE
        # ////////////////////////////
        raw_input("Connect port 1 to RED-(1) and port 2 to BLUE-(2), then press enter")
        print("Taking data")
        self.trace = []
        self.trace_data = []
        self.trace1 = 0.0; self.trace2 = 0.0; self.trace3 = 0.0;        
        self.my_instr.write("S21")          # S21 measurement
        self.my_instr.write("LINM")         # Linear magnitude
        self.my_instr.write("IFBW 100HZ")   # IF bandwidth set to 100Hz
        self.my_instr.write("AUTO")         # Auto scale
        self.my_instr.write("WAIT")         # Wait for one clean sweep

        self.my_instr.write("AVERREST")     # reset the averaging 
        self.my_instr.write("AUTO")         # Auto scale
        time.sleep(4)
        self.my_instr.write("AVERREST")     # reset the averaging 
        time.sleep(self.instr_avg_wait_time)
        self.my_instr.write("WAIT")         # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace1+=i
                self.trace_data.extend([i])
        self.trace1_avg = round(self.trace1/self.dat_point, self.roundpoint)
        self.trace1_avg_str = "{x:.{width}f}".format(width=self.roundpoint, x=self.trace1_avg)
        print(self.trace1_avg_str)
        test1["S21"] = self.trace1_avg
        test1_str["S21"] = self.trace1_avg_str


        self.my_instr.write("AVERREST")  # reset the averaging 
        time.sleep(self.instr_avg_wait_time)        
        self.my_instr.write("WAIT")      # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace2+=i
                self.trace_data.extend([i])
        self.trace2_avg = round(self.trace2/self.dat_point, self.roundpoint)
        self.trace2_avg_str = "{x:.{width}f}".format(width=self.roundpoint, x=self.trace2_avg)
        print(self.trace2_avg_str)        
        test2["S21"] = self.trace2_avg
        test2_str["S21"] = self.trace2_avg_str


        self.my_instr.write("AVERREST")  # reset the averaging 
        time.sleep(self.instr_avg_wait_time)
        self.my_instr.write("WAIT")      # Wait for one clean sweep
        self.my_instr.ask("*OPC?")     
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace3+=i
                self.trace_data.extend([i])
        self.trace3_avg = round(self.trace3/self.dat_point, self.roundpoint)
        self.trace3_avg_str = "{x:.{width}f}".format(width=self.roundpoint, x=self.trace3_avg)
        print(self.trace3_avg_str)        
        test3["S21"] = self.trace3_avg
        test3_str["S21"] = self.trace3_avg_str
        print("\n\n")        

        # ////////////////////////////
        # Measuring RED to GREEN
        # ////////////////////////////            
        raw_input("Connect port 1 to RED-(1) and port 2 to GREEN-(4), then press enter")
        print("Taking data")
        self.trace = []
        self.trace_data = []
        self.trace1 = 0.0; self.trace2 = 0.0; self.trace3 = 0.0;
        self.my_instr.write("AVERREST")  # reset the averaging 
        self.my_instr.write("AUTO")        
        time.sleep(4)
        self.my_instr.write("AVERREST")     # reset the averaging 
        time.sleep(self.instr_avg_wait_time) 
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace1+=i
                self.trace_data.extend([i])
        self.trace1_avg = round(self.trace1/self.dat_point, self.roundpoint)
        self.trace1_avg_str = "{x:.{width}f}".format(width=self.roundpoint, x=self.trace1_avg)
        print(self.trace1_avg_str)
        test1["S41"] = self.trace1_avg
        test1_str["S41"] = self.trace1_avg_str

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
        self.trace2_avg = round(self.trace2/self.dat_point, self.roundpoint)
        self.trace2_avg_str = "{x:.{width}f}".format(width=self.roundpoint, x=self.trace2_avg)
        print(self.trace2_avg_str)        
        test2["S41"] = self.trace2_avg
        test2_str["S41"] = self.trace2_avg_str
        

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
        self.trace3_avg = round(self.trace3/self.dat_point, self.roundpoint)
        self.trace3_avg_str = "{x:.{width}f}".format(width=self.roundpoint, x=self.trace3_avg)
        print(self.trace3_avg_str)        
        test3["S41"] = self.trace3_avg
        test3_str["S41"] = self.trace3_avg_str
        print("\n\n")
        
        # ////////////////////////////
        # Measuring YELLOW to GREEN
        # ////////////////////////////        
        raw_input("Connect port 1 to YELLOW-(3) and port 2 to GREEN-(4), then press enter")
        print("Taking data")
        self.trace = []
        self.trace_data = []
        self.trace1 = 0.0; self.trace2 = 0.0; self.trace3 = 0.0;
        
        self.my_instr.write("AVERREST")  # reset the averaging 
        self.my_instr.write("AUTO")        
        time.sleep(4)
        self.my_instr.write("AVERREST")     # reset the averaging 
        time.sleep(self.instr_avg_wait_time)
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace1+=i
                self.trace_data.extend([i])
        self.trace1_avg = round(self.trace1/self.dat_point, self.roundpoint)
        self.trace1_avg_str = "{x:.{width}f}".format(width=self.roundpoint, x=self.trace1_avg)
        print(self.trace1_avg_str)
        test1["S43"] = self.trace1_avg
        test1_str["S43"] = self.trace1_avg_str


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
        self.trace2_avg = round(self.trace2/self.dat_point, self.roundpoint)
        self.trace2_avg_str = "{x:.{width}f}".format(width=self.roundpoint, x=self.trace2_avg)
        print(self.trace2_avg_str)        
        test2["S43"] = self.trace2_avg
        test2_str["S43"] = self.trace2_avg_str
        

        self.my_instr.write("AVERREST")  # reset the averaging 
        time.sleep(self.instr_avg_wait_time) 
        self.my_instr.write("WAIT")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace3+=i
                self.trace_data.extend([i])
        self.trace3_avg = round(self.trace3/self.dat_point, self.roundpoint)
        self.trace3_avg_str = "{x:.{width}f}".format(width=self.roundpoint, x=self.trace3_avg)
        print(self.trace3_avg_str)        
        test3["S43"] = self.trace3_avg
        test3_str["S43"] = self.trace3_avg_str
        print("\n\n")

        # ////////////////////////////
        # Measuring YELLOW to BLUE
        # ////////////////////////////        
        raw_input("Connect port 1 to YELLOW-(3) and port 2 to BLUE-(2), then press enter")
        print("Taking data")
        self.trace = []
        self.trace_data = []
        self.trace1 = 0.0; self.trace2 = 0.0; self.trace3 = 0.0;

        self.my_instr.write("AVERREST")  # reset the averaging 
        self.my_instr.write("AUTO")
        time.sleep(4)
        self.my_instr.write("AVERREST")     # reset the averaging         
        time.sleep(self.instr_avg_wait_time)
        self.my_instr.write("WAIT")          # Wait for one clean sweep
        self.my_instr.ask("*OPC?")
        self.trace = self.my_instr.ask_for_values("OUTPFORM")
        self.trace_len = len(self.trace)
        for i in self.trace:
            if (i != 0.0):
                self.trace1+=i
                self.trace_data.extend([i])
        self.trace1_avg = round(self.trace1/self.dat_point, self.roundpoint)
        self.trace1_avg_str = "{x:.{width}f}".format(width=self.roundpoint, x=self.trace1_avg)
        print(self.trace1_avg_str)
        test1["S23"] = self.trace1_avg
        test1_str["S23"] = self.trace1_avg_str


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
        self.trace2_avg = round(self.trace2/self.dat_point, self.roundpoint)
        self.trace2_avg_str = "{x:.{width}f}".format(width=self.roundpoint, x=self.trace2_avg)
        print(self.trace2_avg_str)        
        test2["S23"] = self.trace2_avg
        test2_str["S23"] = self.trace2_avg_str
        

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
        self.trace3_avg = round(self.trace3/self.dat_point, self.roundpoint)
        self.trace3_avg_str = "{x:.{width}f}".format(width=self.roundpoint, x=self.trace3_avg)
        print(self.trace3_avg_str)        
        test3["S23"] = self.trace3_avg
        test3_str["S23"] = self.trace3_avg_str
        print("\n\n")      
        
        #Changing back the timeout timer
        self.instrument_timeout = self.instrument_timeout_def
        self.my_instr.timeout = self.instrument_timeout
        #print("Time out timer is changed back to %s sec" %self.my_instr.timeout)
        mm_conv = (10**3)

        x1 = round(self.BPM_pmcc*((test1["S41"]-test1["S21"])+(test1["S43"]-test1["S23"]))/(test1["S21"]+test1["S41"]+test1["S43"]+test1["S23"]), self.roundpoint)
        y1 = round(self.BPM_pmcc*((test1["S41"]-test1["S43"])+(test1["S21"]-test1["S23"]))/(test1["S21"]+test1["S41"]+test1["S43"]+test1["S23"]), self.roundpoint)
        
        x2 = round(self.BPM_pmcc*((test2["S41"]-test2["S21"])+(test2["S43"]-test2["S23"]))/(test2["S21"]+test2["S41"]+test2["S43"]+test2["S23"]), self.roundpoint)
        y2 = round(self.BPM_pmcc*((test2["S41"]-test2["S43"])+(test2["S21"]-test2["S23"]))/(test2["S21"]+test2["S41"]+test2["S43"]+test2["S23"]), self.roundpoint)
        
        x3 = round(self.BPM_pmcc*((test3["S41"]-test3["S21"])+(test3["S43"]-test3["S23"]))/(test3["S21"]+test3["S41"]+test3["S43"]+test3["S23"]), self.roundpoint)
        y3 = round(self.BPM_pmcc*((test3["S41"]-test3["S43"])+(test3["S21"]-test3["S23"]))/(test3["S21"]+test3["S41"]+test3["S43"]+test3["S23"]), self.roundpoint)
                
        x_avg = round((x1+x2+x3)/3, self.roundpoint)
        y_avg = round((y1+y2+y3)/3, self.roundpoint)
        
        x1 = "{x:.{width}f}".format(width=self.roundpoint, x=x1)
        x2 = "{x:.{width}f}".format(width=self.roundpoint, x=x2)
        x3 = "{x:.{width}f}".format(width=self.roundpoint, x=x3)
        y1 = "{x:.{width}f}".format(width=self.roundpoint, x=y1)
        y2 = "{x:.{width}f}".format(width=self.roundpoint, x=y2)
        y3 = "{x:.{width}f}".format(width=self.roundpoint, x=y3)

        x_avg = "{x:.{width}f}".format(width=self.roundpoint, x=x_avg)
        y_avg = "{x:.{width}f}".format(width=self.roundpoint, x=y_avg)

        print("First sets of sample data:\n\n")
        print(test1_str)
        print("Second sets of sample data:\n\n")
        print(test2_str)
        print("Third sets of sample data:\n\n")
        print(test3_str)
        print("X center(mm) for\n1st set: "+x1+",\n2nd set: "+x1+",\n3rd set: "+x1+"\n")
        print("Y center(mm) for\n1st set: "+y1+",\n2nd set: "+y1+",\n3rd set: "+y1+"\n")
        print("X average center(mm): "+x_avg+"\n")
        print("Y average center(mm): "+y_avg+"\n")
  
        self.BPM_record.write("Record format: \n")
        self.BPM_record.write("Red->Blue, Red->Green, Yel->Blue, Yel->Green\n")
        self.BPM_record.write(str(test1_str))
        self.BPM_record.write("\n")
        self.BPM_record.write(str(test2_str))
        self.BPM_record.write("\n")
        self.BPM_record.write(str(test3_str))
        self.BPM_record.write("\n\n")
        self.BPM_record.write("X center(mm):\n")
        self.BPM_record.write(x1+", "+x2+", "+x3+"\n")
        self.BPM_record.write("Y center(mm):\n")
        self.BPM_record.write(y1+", "+y2+", "+y3+"\n")
        
        self.BPM_record.write("X average center(mm): "+x_avg+"\n")
        self.BPM_record.write("Y average center(mm): "+y_avg+"\n\n")

        self.BPM_record.write("<dbFields>\n")
        self.BPM_record.write("Date,PCMM,Frequency,Horizontal Center,Vertical Center\n")
        self.BPM_record.write(str(self.rec_time_stampe)+","+self.BPM_pmcc_str+","+str(self.center_freq)+","+str(x_avg)+","+str(y_avg)+"\n")
        self.BPM_record.write("</dbFields>")