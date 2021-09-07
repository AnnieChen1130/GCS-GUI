from tkinter import *
from threading import *
#!/usr/bin/env python
import time

import serial

#################################### Set up Serial #####################################################
ser = serial.Serial(
    
    port='/dev/ttyUSB0',
    baudrate = 9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1             
 )

# allows reading the serial fully and avoid missing any bytes. *** MUST USE \n AT THE END OF LINE ***
def serialread():
    t_end = time.time() + 4             #set timer of 4 seconds
    time.sleep(.001)                    # delay of 1ms
    val = ser.readline()                # read complete line from serial output
    while not '\n'in str(val):         # check if full data is received. 
        # This loop is entered only if serial read value doesn't contain \n
        # which indicates end of a sentence. 
        # str(val) - val is byte where string operation to check `\\n` 
        # can't be performed
        time.sleep(.001)                # delay of 1ms 
        temp = ser.readline()           # check for serial output.
        if temp.decode():       # if temp is not empty.
            val = (val.decode()+temp.decode()).encode()
            # requrired to decode, sum, then encode because
            # long values might require multiple passes
        elif time.time() < t_end:       # break loop if alloted time for serial reading is passed.
            break
    val = val.decode()                  # decoding from bytes
    val = val.strip()                   # stripping leading and trailing spaces.
    return val



############################## Set up GUI ####################################################

root = Tk()
root.geometry("700x600")
root.title(" GCS ")


launchSearch = 0
launchRescue = 0

searchThreadControl = 1
rescueThreadControl = 1

def threading():
    t1 = Thread(target=Run_Search_Thread)
    t2 = Thread(target=Run_Rescue_Thread)
    t1.start()
    t2.start()   

################### Search Drone Functions ############################
def Run_Search_Thread():
    
    while searchThreadControl:
        Search_Launch()  
    
    
def Search_Launch():
    
    i = 0
    missionSignal = 'on\n'
    mission_signal_respond_from_search = "no"
    
    while not launchSearch:
        if not searchThreadControl:
            break
        print("launchSearch ", launchSearch)
        searchTxt.insert(END,"SEARCH Launcher is not running!\n")
        searchTxt.see(END)
        time.sleep(2)

    if launchSearch and searchThreadControl:
        searchTxt.insert(END,"\nSEARCH Launcher Running!\n\n")
        
        #Send signal to powerup the drone
        ser.write(missionSignal.encode())
        time.sleep(.001)    #add delay to allow it bytes to be fully sent.
        print("GCS tries to powerup Search Drone and has it start mission")
        searchTxt.insert(END,"GCS tries to powerup Search Drone and has it start mission\n\n")
        searchTxt.see(END)
        
        while mission_signal_respond_from_search  != "yes":
            if not launchSearch:
                break
            
            mission_signal_respond_from_search=serialread()
            searchTxt.insert(END,"Waiting for Fire Detection to respond {}\n".format(i))
            searchTxt.see(END)
            i += 1
            
            if i >5:
                mission_signal_respond_from_search  = "yes"


        #Get coords
        Received_coords()

        #while launchSearch:
        #    pass
        
    if not launchSearch:
        searchTxt.insert(END,"\nExiting SEARCH program!"+ '\n')
        searchTxt.see(END)

    #GPIO.cleanup()
        
        
def Received_coords():
    coords_received_from_search = 0
    count = 0

    while not coords_received_from_search:

        if not launchSearch:
            break
        
        x = ser.read(34).decode()
       
        if x: # CHECK FOR "NOT EMPTY"; x should be an array containing lat and lon coordinates
                # ON THE Sending SIDE, it should be either:
                #	x(1) = 34.0425919 # HARDCODE VERSION
                #	x(2) = -117.8121552 # HARDCODE VERSION
                #   x(1) = vehicle.location.global_relative_frame.lat  # "get the current latitude from PIXHAWK" VERSION 
                #	x(2) = vehicle.location.global_relative_frame.lon  # "get the current longitude from PIXHAWK" VERSION
            parsed_string = x.split()
            if parsed_string[0] == "GCS": # CHECKING if we have received the correct string
                print ('Coordinate recieved ON GROUND CONTROL STATION!')
                searchTxt.insert(END,"Coordinate recieved ON GROUND CONTROL STATION!\n")               
                searchTxt.see(END)
                coords_received_from_search = 1
        
        else:
            print ('Waiting for coordination from SEARCH... {} second'.format(count))
            searchTxt.insert(END,'Waiting for coordination from SEARCH... {} second\n'.format(count))
            searchTxt.see(END)
            time.sleep(1)
            count = count+1
            
            if count > 1:
                coords_received_from_search = 1
                x = "GCS 35.0 149.0"
                parsed_string = x.split()
                
         
    if coords_received_from_search:     
        # read coordinates
        lat = float(parsed_string[1])
        lon = float(parsed_string[2])
        
        #convert coord to string
        coords = "Target Coordinate:" + " " + str(lat) + " " + str(lon)
        searchTxt.insert(END,'\n' + coords + '\n')
        searchTxt.see(END)
        
        
        '''
        # prints coordinates to file
        f = open("/home/pi/Desktop/coordoutput/output.txt", "w")
        print(coords,file=f)
        f.close()'''
        
        print("Coordinates saved to file")
        
        global searchThreadControl
        searchThreadControl = 0




################### Rescue Drone Functions ############################
def Run_Rescue_Thread():
    
    while rescueThreadControl:
        Rescue_Launch()  


def Read_Coord():

         
    rescueTxt.insert(END,"Trying to read coordinates from file\n")
    rescueTxt.see(END)
    print ("Trying to read coordinates from file")    
    
    f = open("/home/pi/Desktop/output.txt", "r")
    send_coord = f.readline()
    f.close()

    #send_coord = 1
    coords_received_on_rescue = 0
    count = 0

    if send_coord:
        while not coords_received_on_rescue:
            ser.write(send_coord.encode())
            rescueTxt.insert(END,'Sending coordinates to RESCUE... {}\n'.format(count))
            rescueTxt.see(END)
            time.sleep(1)
            count = count+1

            x = ser.read(8).decode()
            
            if count>2:
                x = "received"
                      
            if x == "received":
                coords_received_on_rescue = 1
                rescueTxt.insert(END,"Coordinates received ON RESCUE DRONE\n")
                rescueTxt.see(END)                
            else:
                rescueTxt.insert(END,"Could not read coordinates from file\n")
                rescueTxt.see(END)

def Rescue_Launch():

    count = 0
    
    while not launchRescue:
        print("launchRescue ", launchRescue)
        rescueTxt.insert(END,"RESCUE Launcher is not running!\n")
        rescueTxt.see(END)
        time.sleep(2)

    if launchRescue:
        rescueTxt.insert(END,"\nRESCUE Launcher Running!\n")
        rescueTxt.see(END)

        #Send signal to powerup the drone
        ser.write(powerup.encode())
        time.sleep(.001)    #add delay to allow it bytes to be fully sent.
        print("RESCUE Drone PowerUp")
        rescueTxt.insert(END,"\nRESCUE Drone PowerUp!\n\n")
        rescueTxt.see(END)

        Read_Coord()

        while launchRescue:
            pass
        
    if not launchRescue:
        rescueTxt.insert(END,"\nExiting RESCUE program!"+ '\n')
        rescueTxt.see(END)

################### GUI Functions ##########################
def Search_Start():
    global launchSearch
    launchSearch = 1
    print("launchSearch ", launchSearch)
    return

def Search_Stop():
    global launchSearch
    launchSearch = 0
    print("launchSearch ", launchSearch)
    return

def Rescue_Start():
    global launchRescue
    launchRescue = 1
    print("launchRescue ", launchRescue)
    return

def Rescue__Stop():
    global launchRescue
    launchRescue = 0
    print("launchRescue ", launchRescue)
    return

def Control_Search_Thread():
    global searchThreadControl
    if searchThreadControl:
        searchThreadControl = 0
    else:
        searchThreadControl = 1
    print("searchThreadControl ", searchThreadControl)
    return

def Control_Rescue_Thread():
    global rescueThreadControl
    rescueThreadControl = 1
    print("rescueThreadControl ", rescueThreadControl)
    return


################## Main ####################################
Label1 = Label(text = " Search Drone ")
Label2 = Label(text = " Rescure Drone ")
searchTxt = Text(root,height = 30,
                width = 40,
                bg = "light yellow")
  
rescueTxt = Text(root, 
                height = 30,
                width = 40,
              bg = "light cyan")

  
searchLaunchButton = Button(root,  
                 text ="SEARCH Launch",
                 command = lambda:Search_Start())
searchStopButton = Button(root,  
                 text ="SEARCH Stop",
                 command = lambda:Search_Stop())
rescueLaunchButton = Button(root,  
                 text ="RESCUE Launch",
                 command = lambda:Rescue_Start())
rescueStopButton = Button(root,  
                 text ="RESCUE Stop",
                 command = lambda:Rescue__Stop())

searchThreadButton = Button(root,  
                 text ="Search Thread",
                 command = lambda:Control_Search_Thread())

rescueThreadButton = Button(root,  
                 text ="Search Thread",
                 command = lambda:Control_Rescue_Thread())

  
Label1.grid(row=0, column=0)
Label2.grid(row=0, column=1)
searchTxt.grid(row=1, column=0,padx=5,pady=5)
rescueTxt.grid(row=1, column=1,padx=5,pady=5)
searchLaunchButton.grid(row=2, column=0)
rescueLaunchButton.grid(row=2, column=1)
searchStopButton.grid(row=3, column=0)
rescueStopButton.grid(row=3, column=1)
searchThreadButton.grid(row=4, column=0)
rescueThreadButton.grid(row=4, column=1)

root.after(1, threading)
root.mainloop()    
