import tkinter as tk 

import cv2  
from PIL import Image
from PIL import ImageTk
import threading
import os

class MainWindow():
    def __init__(self, window, cap):
        self.window = window
        self.cap = cap
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.interval = 10 # Interval in ms to get the latest frame
        # Create canvas for image
        self.canvas = tk.Canvas(self.window, width=600, height=400)
        self.canvas.grid(row=0, column=0)
        # Update image on canvas
        root.after(self.interval, self.update_image)
        self.button = tk.Button()

    def update_image(self):    
        # Get the latest frame and convert image format
        self.OGimage = cv2.cvtColor(self.cap.read()[1], cv2.COLOR_BGR2RGB) # to RGB
        self.OGimage = Image.fromarray(self.OGimage) # to PIL format
        self.image = self.OGimage.resize((600, 400), Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(self.image) # to ImageTk format
        # Update image
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image)
        # Repeat every 'interval' ms
        self.window.after(self.interval, self.update_image)

#def run_decoding(): 
    #os.system("ffmpeg -i rtsp://192.168.1.10?tcp -codec copy -f mpegts udp://127.0.0.1:5000 &")


if __name__ == "__main__":
    #my_cam = ONVIFCamera('192.168.1.10', 80, 'gemer.daniel@gmail.com', 'dg24111998')
    #media = my_cam.create_media_service()
    #ptz = my_cam.create_ptz_service()
    #media_profile = media.GetProfiles()[0]

    # Get PTZ configuration options for getting continuous move range
    #request = ptz.create_type('GetConfigurationOptions')
    #request.ConfigurationToken = media_profile.token
    #ptz_configuration_options = ptz.GetConfigurationOptions(request)

    #request = ptz.create_type('ContinuousMove')
    #request.ProfileToken = media_profile._token

    #ptz.Stop({'ProfileToken': media_profile._token})
    #p1 = threading.Thread(target=run_decoding)
    #p1.start()
    root = tk.Tk()
    camSet2='rtsp://admin:950793@192.168.43.21:554/live/profile.0'
    cap = cv2.VideoCapture(camSet2)
    MainWindow(root, cap)
    root.mainloop()