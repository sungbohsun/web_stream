from PyQt5 import QtCore, QtGui, QtWidgets
import qdarkstyle
from threading import Thread
from collections import deque
from datetime import datetime
import time
import sys
import cv2, torch
from PIL import Image as im
from utils.augmentations import letterbox
import imutils
import numpy as np

model = torch.hub.load('./models', 'custom', path='helmet_head_person_s.pt',source='local')
# Split string to float
def plot_box(img,pred_xywhn):
    for shot in pred_xywhn:
        x, y, w, h, p, _ = shot
        if p > 0.4:

            l = int((x - w / 2) * img.shape[1])
            r = int((x + w / 2) * img.shape[1])
            t = int((y - h / 2) * img.shape[0])
            b = int((y + h / 2) * img.shape[0])

            if l < 0:
                l = 0
            if r > img.shape[1] - 1:
                r = img.shape[1] - 1
            if t < 0:
                t = 0
            if b > img.shape[0] - 1:
                b = img.shape[0] - 1
            if _ == 0 :
                cv2.rectangle(img, (l, t), (r, b), (255, 0, 0), 1)
            if _ == 1 :
                cv2.rectangle(img, (l, t), (r, b), (0, 0, 255), 1)
            if _ == 2 :
                cv2.rectangle(img, (l, t), (r, b), (0, 255, 0), 1)

        return img

class CameraWidget(QtWidgets.QMainWindow):
    """Independent camera feed
    Uses threading to grab IP camera frames in the background
    @param width - Width of the video frame
    @param height - Height of the video frame
    @param stream_link - IP/RTSP/Webcam link
    @param aspect_ratio - Whether to maintain frame aspect ratio or force into fraame
    """

    def __init__(self, width, height, stream_link=0, aspect_ratio=False, parent=None, deque_size=1):
        super(CameraWidget, self).__init__(parent)

        # Initialize deque used to store frames read from the stream
        self.deque = deque(maxlen=deque_size)

        # Slight offset is needed since PyQt layouts have a built in padding
        # So add offset to counter the padding 
        self.offset = 16
        self.screen_width = width - self.offset
        self.screen_height = height - self.offset
        self.maintain_aspect_ratio = aspect_ratio

        self.camera_stream_link = stream_link

        # Flag to check if camera is valid/working
        self.online = False
        self.capture = None
        self.video_frame = QtWidgets.QLabel()

        self.load_network_stream()

        # Start background frame grabbing
        self.get_frame_thread = Thread(target=self.get_frame, args=())
        self.get_frame_thread.daemon = True
        self.get_frame_thread.start()

        # Periodically set video frame to display
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.set_frame)
        self.timer.start(.5)

        print('Started camera: {}'.format(self.camera_stream_link))

    def load_network_stream(self):
        """Verifies stream link and open new stream if valid"""

        def load_network_stream_thread():
            if self.verify_network_stream(self.camera_stream_link):
                self.capture = cv2.VideoCapture(self.camera_stream_link)
                self.online = True
        self.load_stream_thread = Thread(target=load_network_stream_thread, args=())
        self.load_stream_thread.daemon = True
        self.load_stream_thread.start()

    def verify_network_stream(self, link):
        """Attempts to receive a frame from given link"""

        cap = cv2.VideoCapture(link)
        if not cap.isOpened():
            return False
        cap.release()
        return True

    def get_frame(self):
        """Reads frame, resizes, and converts image to pixmap"""
        fpsLimit = 0.5 # throttle limit
        startTime = time.time()
        while True:
            try:
                if self.capture.isOpened() and self.online:
                    # Read next frame from stream and insert into deque
                    status, frame = self.capture.read()
                    if status:
                        nowTime = time.time()
                        if (int(nowTime - startTime)) > fpsLimit:
                            img = letterbox(frame, 640, 64)[0]
                            pred = model(img)
                            frame_ = plot_box(img,pred.xywhn[0])

                            if type(frame_) == np.ndarray:
                                if frame_.any() != None:
                                    self.deque.append(frame_)
                                    print('__',frame_)
                                    print(type(frame_))
                            else :
                                self.deque.append(frame)
                                print('***',frame)
                            startTime = time.time() # reset time
                    else:
                        self.capture.release()
                        self.online = False
                else:
                    # Attempt to reconnect
                    print('attempting to reconnect', self.camera_stream_link)
                    self.load_network_stream()
                    self.spin(2)
                self.spin(.001)
            except AttributeError:
                pass

    def spin(self, seconds):
        """Pause for set amount of seconds, replaces time.sleep so program doesnt stall"""

        time_end = time.time() + seconds
        while time.time() < time_end:
            QtWidgets.QApplication.processEvents()

    def set_frame(self):
        """Sets pixmap image to video frame"""

        if not self.online:
            self.spin(1)
            return

        if self.deque and self.online:
            # Grab latest frame
            frame = self.deque[-1]

            # Keep frame aspect ratio
            if self.maintain_aspect_ratio:
                self.frame = imutils.resize(frame, width=self.screen_width)
            # Force resize
            else:
                self.frame = cv2.resize(frame, (self.screen_width, self.screen_height))

            # Add timestamp to cameras
            cv2.rectangle(self.frame, (self.screen_width-190,0), (self.screen_width,50), color=(0,0,0), thickness=-1)
            cv2.putText(self.frame, datetime.now().strftime('%H:%M:%S'), (self.screen_width-185,37), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), lineType=cv2.LINE_AA)

            # Convert to pixmap and set to video frame
            self.img = QtGui.QImage(self.frame, self.frame.shape[1], self.frame.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
            self.pix = QtGui.QPixmap.fromImage(self.img)
            self.video_frame.setPixmap(self.pix)

    def get_video_frame(self):
        return self.video_frame

def exit_application():
    """Exit program event handler"""

    sys.exit(1)

if __name__ == '__main__':

    # Create main application window
    app = QtWidgets.QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt())
    app.setStyle(QtWidgets.QStyleFactory.create("Cleanlooks"))
    mw = QtWidgets.QMainWindow()
    mw.setWindowTitle('Camera GUI')
    mw.setWindowFlags(QtCore.Qt.FramelessWindowHint)

    cw = QtWidgets.QWidget()
    ml = QtWidgets.QGridLayout()
    cw.setLayout(ml)
    mw.setCentralWidget(cw)
    mw.showMaximized()

    # Dynamically determine screen width/height
    screen_width = QtWidgets.QApplication.desktop().screenGeometry().width()
    screen_height = QtWidgets.QApplication.desktop().screenGeometry().height()

    # Create Camera Widgets 
    username = 'Your camera username!'
    password = 'Your camera password!'

    # Stream links
    camera0 = 'rtsp://10.96.212.247:5555/unicast'.format(username, password)
    camera1 = 'rtsp://10.96.212.249:5555/unicast'.format(username, password)
#    camera2 = 'rtsp://10.96.212.247:5555/unicast'.format(username, password)
#    camera3 = 'rtsp://10.96.212.247:5555/unicast'.format(username, password)
#    camera4 = 'rtsp://10.96.212.249:5555/unicast'.format(username, password)
#    camera5 = 'rtsp://10.96.212.249:5555/unicast'.format(username, password)
#    camera6 = 'rtsp://10.96.212.249:5555/unicast'.format(username, password)
#    camera7 = 'rtsp://10.96.212.249:5555/unicast'.format(username, password)

    # Create camera widgets
    print('Creating Camera Widgets...')
    zero = CameraWidget(screen_width//2, screen_height//2, camera0)
    one = CameraWidget(screen_width//2, screen_height//2, camera1)
 #   two = CameraWidget(screen_width//3, screen_height//3, camera2)
 #   three = CameraWidget(screen_width//3, screen_height//3, camera3)
 #   four = CameraWidget(screen_width//3, screen_height//3, camera4)
 #   five = CameraWidget(screen_width//3, screen_height//3, camera5)
 #   six = CameraWidget(screen_width//3, screen_height//3, camera6)
 #   seven = CameraWidget(screen_width//3, screen_height//3, camera7)

 #   print('Creating Camera Widgets...')
 #   zero = CameraWidget(screen_width//3, screen_height//3, 0)
 #   one = CameraWidget(screen_width//3, screen_height//3, 0)
 #   two = CameraWidget(screen_width//3, screen_height//3, 0)
 #   three = CameraWidget(screen_width//3, screen_height//3, 0)
 #   four = CameraWidget(screen_width//3, screen_height//3, 0)
 #   five = CameraWidget(screen_width//3, screen_height//3, 0)
 #   six = CameraWidget(screen_width//3, screen_height//3, 0)
 #   seven = CameraWidget(screen_width//3, screen_height//3, 0)

    # Add widgets to layout
    print('Adding widgets to layout...')
    ml.addWidget(zero.get_video_frame(),0,0,1,1)
    ml.addWidget(one.get_video_frame(),0,1,1,1)
  #  ml.addWidget(two.get_video_frame(),0,2,1,1)
  #  ml.addWidget(three.get_video_frame(),1,0,1,1)
  #  ml.addWidget(four.get_video_frame(),1,1,1,1)
  #  ml.addWidget(five.get_video_frame(),1,2,1,1)
  #  ml.addWidget(six.get_video_frame(),2,0,1,1)
  #  ml.addWidget(seven.get_video_frame(),2,1,1,1)

    print('Verifying camera credentials...')

    mw.show()

    QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+Q'), mw, exit_application)

    if(sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()