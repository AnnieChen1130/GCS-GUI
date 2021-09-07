from tkinter import *
from threading import *
#!/usr/bin/env python
import time

import serial

import cv2
import PIL.Image, PIL.ImageTk

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



############################## Thread ####################################################

def threading():
    t1 = Thread(target=Run_Search_Thread)
    t2 = Thread(target=Run_Rescue_Thread)
    t3 = Thread(target=Rescue_Camera)
        
    t1.start()
    t2.start()
    t3.start()

################### Search Drone Functions ############################

def Run_Search_Thread():
    
    #while searchRestartLaunch:
    while True:
        Search_Launch()   
    
    
    
def Search_Launch():
    
    i = 0
    start_mission_singal = 'on\n'
    receive_mission_signal_from_search = "no"
    
    while not launchSearch:
        if not searchRestartLaunch:
            break
        print("launchSearch ", launchSearch)
        searchTxt.insert(END,"Fire Detection Launcher is not running!\n")
        searchTxt.see(END)
        time.sleep(2)

    if launchSearch and searchRestartLaunch:
        searchTxt.insert(END,"\nFire Detection Launcher Running!\n\n")
        
        #Send signal to powerup the drone
        ser.write(start_mission_singal.encode())
        time.sleep(.001)    #add delay to allow it bytes to be fully sent.
        print("GCS asks Fire Detection Drone to start mission")
        searchTxt.insert(END,"GCS asks Fire Detection Drone to start mission\n\n")
        searchTxt.see(END)
        
        while receive_mission_signal_from_search != "GCS Search yes":
            if not launchSearch:
                break
            
            searchTxt.insert(END,"Waiting for Fire Detection to respond {}\n".format(i))
            searchTxt.see(END)
            i += 1
            
            #Read respond from search drone
            receive_mission_signal_from_search = ser.read(34).decode()        
            
            global search_resend_signal
            if search_resend_signal:
                ser.write(start_mission_singal.encode())
                searchTxt.insert(END,"\nGCS resend start mission signal\n\n")
                searchTxt.see(END)
                search_resend_signal = 0
                i = 0
            
            #Test without Xbee
            if i > 5:
                receive_mission_signal_from_search  = "GCS Search yes"
                
            if receive_mission_signal_from_search  == "GCS Search yes":
                searchTxt.insert(END,"\nReceive respond from Fire Detection Drone\n\n")


        #Get coords
        Received_coords()
        
        searchTxt.insert(END,"\nFire Detection Drone RTL")
        searchTxt.see(END)
        
    if not launchSearch:
        searchTxt.insert(END,"\nExiting Fire Detection program!"+ '\n')
        searchTxt.see(END)

        
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
            print ('Waiting for coordination from Fire Detection... {} second'.format(count))
            searchTxt.insert(END,'Waiting for coordination from Fire Detection... {} second\n'.format(count))
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
            
        
        # prints coordinates to file
        f = open("/home/pi/Desktop/output.txt", "w")
        print(coords,file=f)
        f.close()
        
        print("Coordinates saved to file")
        searchTxt.insert(END, "Coordinates saved to file" + '\n')
        searchTxt.see(END)
        time.sleep(1)
        
        global searchRestartLaunch
        searchRestartLaunch = 0


################### Rescue Drone Functions ############################
def Run_Rescue_Thread():
    
    while True:
        Rescue_Launch()  

def Rescue_Launch():

    file = open("/home/pi/Desktop/output.txt","r+")
    file.truncate(0)
    file.close()

    count = 0
    start_mission = 'on\n'
    receive_mission_signal_from_rescue = "no"
    
    while not launchRescue:
        if not rescueRestartLaunch:
            break
        print("launchRescue ", launchRescue)
        rescueTxt.insert(END,"Fire Suppression Launcher is not running!\n")
        rescueTxt.see(END)
        time.sleep(2)

    if launchRescue and rescueRestartLaunch:
        rescueTxt.insert(END,"\nFire Suppression Launcher Running!\n\n")
        rescueTxt.see(END)
        
        #Send signal to powerup the drone
        ser.write(start_mission.encode())
        time.sleep(.001)    #add delay to allow it bytes to be fully sent.
        print("GCS asks Fire Suppression Drone to start mission")
        rescueTxt.insert(END,"GCS asks Fire Suppression Drone to start mission\n\n")
        rescueTxt.see(END)
        
        while receive_mission_signal_from_rescue != "GCS Rescue yes":
            if not launchRescue:
                break
            
            rescueTxt.insert(END,"Waiting for Fire Suppression to respond {}\n".format(count))
            rescueTxt.see(END)
            count += 1
            
            #Read respond from search drone
            receive_mission_signal_from_rescue = ser.read(34).decode()        

            global rescue_resend_signal
            if rescue_resend_signal:
                ser.write(start_mission.encode())
                rescueTxt.insert(END,"\nGCS resend start mission signal\n\n")
                rescueTxt.see(END)
                rescue_resend_signal = 0
                count = 0

            
            #Test without Xbee
            if count > 5:
                receive_mission_signal_from_rescue  = "GCS Rescue yes"
                
            if receive_mission_signal_from_rescue  == "GCS Rescue yes":
                rescueTxt.insert(END,"\nReceive respond from Fire Suppression Drone\n\n")

        #Read coords
        Read_Coord()
        
        rescueTxt.insert(END,"\nFire Suppression Drone start suppression mission")
        rescueTxt.see(END)
        
    if not launchSearch:
        rescueTxt.insert(END,"\nExiting Fire Suppression program!"+ '\n')
        rescueTxt.see(END)


def Read_Coord():
    
    send_coord = 0
    count = 0
    while not send_coord:
        rescueTxt.insert(END,"Trying to read coordinates from file\n".format(count))
        rescueTxt.see(END)
        time.sleep(1)
        count += 1  
        
        f = open("/home/pi/Desktop/output.txt", "r")
        send_coord = f.readline()
        f.close()

    #send_coord = 1
    coords_received_on_rescue = 0
    count = 0

    if send_coord:
        
        rescueTxt.insert(END,"\nCoordinates are readed from file\n\n")
        rescueTxt.see(END)        
        
        while not coords_received_on_rescue:
            
            #Send coordinates to Rescue
            ser.write(send_coord.encode())
            rescueTxt.insert(END,'Sending coordinates to Fire Suppression... {}\n'.format(count))
            rescueTxt.see(END)
            time.sleep(2)
            count += 1

            x = ser.read(8).decode()
            
            if count>5:
                x = "received"
                      
            if x == "received":
                coords_received_on_rescue = 1
                rescueTxt.insert(END,"\nCoordinates received ON Fire Suppression DRONE\n")
                rescueTxt.see(END)                
            '''
            else:
                rescueTxt.insert(END,"Waiting Fire Suppress to received the Coordinates\n")
                rescueTxt.see(END)
            '''

        global rescueRestartLaunch
        rescueRestartLaunch = 0

################### Search and Rescue Functions ##########################
launchSearch = 0
launchRescue = 0
search_resend_signal = 0
rescue_resend_signal = 0

def Search_Start():
    global launchSearch
    if launchSearch:
        launchSearch = 0
    else:
        launchSearch = 1
    print("launchSearch ", launchSearch)
    return

def Search_Resend_Signal():
    global search_resend_signal
    if search_resend_signal:
        search_resend_signal = 0
    else:
        search_resend_signal = 1
    print("search_resend_signal ", search_resend_signal)
    return

def Rescue_Start():
    global launchRescue
    if launchRescue:
        launchRescue = 0
    else:
        launchRescue = 1
    print("launchRescue ", launchRescue)
    return

def Rescue_Resend_Signal():
    global rescue_resend_signal
    if rescue_resend_signal:
        rescue_resend_signal = 0
    else:
        rescue_resend_signal = 1
    print("rescue_resend_signal ", rescue_resend_signal)
    return

searchRestartLaunch = 1
rescueRestartLaunch = 1

def Control_Search_Thread():
    global searchRestartLaunch
    if searchRestartLaunch:
        searchRestartLaunch = 0
    else:
        searchRestartLaunch = 1
    print("searchRestartLaunch ", searchRestartLaunch)
    return

def Control_Rescue_Thread():
    global rescueRestartLaunch
    if rescueRestartLaunch:
        rescueRestartLaunch = 0
    else:
        rescueRestartLaunch = 1
    print("rescueRestartLaunch ", rescueRestartLaunch)
    return


################################ Camera #############################################################
def Rescue_Camera():

     # After it is called once, the update method will be automatically called every delay milliseconds
    update(vid)
    

    
def snapshot(vid):
     # Get a frame from the video source
     ret, frame = vid.get_frame()

     if ret:
         cv2.imwrite("frame-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

def update(vid):
     # Get a frame from the video source
     ret, frame = vid.get_frame()

     if ret:
         photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
         canvas.create_image(0, 0, image = photo, anchor = NW)
     delay = 15
     root.after(delay, update(vid))

 
class MyVideoCapture:
     def __init__(self, video_source=0):
         # Open the video source
         self.vid = cv2.VideoCapture(video_source)
         if not self.vid.isOpened():
             raise ValueError("Unable to open video source", video_source)
 
         # Get video source width and height
         self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
         self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
 
     def get_frame(self):
         if self.vid.isOpened():
             ret, frame = self.vid.read()
             if ret:
                 # Return a boolean success flag and the current frame converted to BGR
                 return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
             else:
                 return (ret, None)
         else:
             return (ret, None)
 
     # Release the video source when the object is destroyed
     def __del__(self):
         if self.vid.isOpened():
             self.vid.release()


################## Main ####################################
root = Tk()
#root.geometry("1035x800")
root.title(" GCS ")

frame1 = Frame(root)
frame2 = Frame(root)

Label1 = Label(frame1, text = " Fire Detection Drone ")
Label2 = Label(frame1, text = " Fire Suppression Drone ")

search_map = Frame(frame1, width=400, height=400, bg="blue")#image=img
rescue_map = Frame(frame1, width=400, height=400, bg="green")#image=img

searchTxt = Text(frame1,height = 10,
                width = 50,
                bg = "light yellow")
  
rescueTxt = Text(frame1, 
                height = 10,
                width = 50,
              bg = "light cyan")

  
searchLaunchButton = Button(frame1,  
                 text ="Fire Detection Launch",
                 command = lambda:Search_Start())
searchStopButton = Button(frame1,  
                 text ="Fire Detection Resend Signal",
                 command = lambda:Search_Resend_Signal())
rescueLaunchButton = Button(frame1,  
                 text ="Fire Suppression Launch",
                 command = lambda:Rescue_Start())
rescueStopButton = Button(frame1,  
                 text ="Fire Suppression Resend Signal",
                 command = lambda:Rescue_Resend_Signal())
searchThreadButton = Button(frame1,  
                 text ="Fire Detection Restart Launch",
                 command = lambda:Control_Search_Thread())

rescueThreadButton = Button(frame1,  
                 text ="Fire Suppression Restart Launch",
                 command = lambda:Control_Rescue_Thread())
  
Label1.grid(row=0, column=0)
Label2.grid(row=0, column=1)
search_map.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
rescue_map.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
searchTxt.grid(row=2, column=0,padx=5,pady=5)
rescueTxt.grid(row=2, column=1,padx=5,pady=5)
searchLaunchButton.grid(row=3, column=0)
rescueLaunchButton.grid(row=3, column=1)
searchStopButton.grid(row=4, column=0)
rescueStopButton.grid(row=4, column=1)
searchThreadButton.grid(row=5, column=0)
rescueThreadButton.grid(row=5, column=1)

video_source=0
vid = MyVideoCapture(video_source)

 # Create a canvas that can fit the above video source size
canvas = Canvas(frame2, width = vid.width, height = vid.height)
canvas.grid(row=0, column=0)

 # Button that lets the user take a snapshot
btn_snapshot=Button(frame2, text="Snapshot", width=50, command= lambda: snapshot(vid))
btn_snapshot.grid(row=1, column=0)


frame1.grid(row=0, column=0)
frame2.grid(row=0, column=1)

root.after(1, threading)
root.mainloop()    