import cv2, torch
from PIL import Image as im
from models.experimental import attempt_load
from utils.augmentations import letterbox
import numpy as np
# Model
model = torch.hub.load('ultralytics/yolov5', 'custom', path='helmet_head_person_s.pt')

# Split string to float
def plot_box(img,pred_xywhn):
    for shot in pred_xywhn:
        x, y, w, h, p, _ = shot
        if p > 0.6:

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
                cv2.rectangle(img, (l, t), (r, b), (0, 0, 255), 1)
            if _ == 1 :
                cv2.rectangle(img, (l, t), (r, b), (255, 0, 0), 1)
            if _ == 2 :
                cv2.rectangle(img, (l, t), (r, b), (0, 255, 0), 1)

        return img
    
dispW=680
dispH=480
flip=2
camSet2='rtsp://10.96.212.247:5555/unicast'
cap = cv2.VideoCapture(camSet2)
cap.set(cv2.CAP_PROP_FPS, 1)

ret, frame = cap.read()
avg = cv2.blur(frame, (4, 4))
avg_float = np.float32(avg)

while(cap.isOpened()):
    # 讀取一幅影格
    ret, frame = cap.read()
    while ret == False:
        print("Can't receive frame. Retrying ...")
        cap.release()
        cap = cv2.VideoCapture(camSet2)     
        cap.set(cv2.CAP_PROP_FPS, 1)
    else:
        img = letterbox(frame, 640, 64)[0]
        pred = model(img)
        frame = plot_box(img,pred.xywhn[0])

        # 顯示偵測結果影像
        cv2.imshow('frame', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()