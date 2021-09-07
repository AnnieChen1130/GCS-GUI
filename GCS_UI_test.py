from tkinter import *
from threading import *
#!/usr/bin/env python
import time

import serial

'''
#import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#setting up gpio 2 for button
GPIO.setup(2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(2,GPIO.FALLING,bouncetime=200) #event to detect if button is pushed to avoid spamming button.
'''

ser = serial.Serial(
    
    port='/dev/ttyUSB0',
    baudrate = 9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1             
 )


root = Tk()
root.geometry("700x600")
root.title(" GCS ")


launchSearch = 0
launchRescue = 0

coords_received = 0

def threading():
    t1 = Thread(target=Search_Launch)
    t2 = Thread(target=Rescue_Launch)
    t1.start()
    t2.start()   

################### Search Drone Functions ############################
def Received_coords(coords, count):
    
    global coords_received
    coords_received = 0

    while not coords_received:

        if not launchSearch:
            break
        
        x = ser.read(34).decode()
        #x=0
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
                coords_received = 1
        
        else:
            print ('Waiting for coordination from SEARCH... {} second'.format(count))
            searchTxt.insert(END,'Waiting for coordination from SEARCH... {} second\n'.format(count))
            searchTxt.see(END)
            time.sleep(1)
            count = count+1

            '''
            if count > 15:
                coords_received = 1
                x = "GCS 35.0 149.0"
                parsed_string = x.split()
                '''
         
    if coords_received:     
        # read coordinates
        lat = float(parsed_string[1])
        lon = float(parsed_string[2])
        
        #convert coord to string
        coords = "RESCUE" + " " + str(lat) + " " + str(lon)
        searchTxt.insert(END,'\n' + coords + '\n')
        searchTxt.see(END)
        
        # prints coordinates to file
        f = open("/home/pi/Desktop/coordoutput/output.txt", "w")
        print(coords,file=f)
        f.close()
        
        print("Coordinates saved to file")    

def Search_Launch():
    
    coords = 0
    powerup = 'on\n'
    count = 0

    while not launchSearch:
        print("launchSearch ", launchSearch)
        searchTxt.insert(END,"SEARCH Launcher is not running!\n")
        searchTxt.see(END)
        time.sleep(2)

    if launchSearch:
        searchTxt.insert(END,"\nSEARCH Launcher Running!\n\n")
        
        #Send signal to powerup the drone
        ser.write(powerup.encode())
        time.sleep(.001)    #add delay to allow it bytes to be fully sent.
        print("SEARCH Drone PowerUp")
        searchTxt.insert(END,"SEARCH Drone PowerUp!\n\n")
        searchTxt.see(END)

        #Get coords
        Received_coords(coords, count)

        while launchSearch:
            pass
        
    if not launchSearch:
        searchTxt.insert(END,"\nExiting SEARCH program!"+ '\n')
        searchTxt.see(END)

    #GPIO.cleanup()

################### Rescue Drone Functions ############################
def Read_Coord():

    global coords_received

    while not coords_received:
        rescueTxt.insert(END,"No coords received\n")
        rescueTxt.see(END)
        time.sleep(1)

           
    rescueTxt.insert(END,"Trying to read coordinates from file\n")
    rescueTxt.see(END)
    print ("Trying to read coordinates from file")    
    
    f = open("/home/pi/Desktop/coordoutput/output.txt", "r")
    send_coord = f.readline()
    f.close()

    send_coord = 1

    if send_coord:
        while not coords_received:
            ser.write(send_coord.encode())
            rescueTxt.insert(END,'Sending coordinates... {} second\n'.format(count))
            rescueTxt.see(END)
            time.sleep(1)
            count = count+1

            x = ser.read(8).decode()
            #x = 0
            if x == "received":
                coords_received = 1
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
        #ser.write(powerup.encode())
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
  
Label1.grid(row=0, column=0)
Label2.grid(row=0, column=1)
searchTxt.grid(row=1, column=0,padx=5,pady=5)
rescueTxt.grid(row=1, column=1,padx=5,pady=5)
searchLaunchButton.grid(row=2, column=0)
rescueLaunchButton.grid(row=2, column=1)
searchStopButton.grid(row=3, column=0)
rescueStopButton.grid(row=3, column=1)


root.after(1, threading)
root.mainloop()    