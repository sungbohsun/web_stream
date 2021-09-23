#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, Response
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
            
class VideoCamera(object):
    def __init__(self):
        # 通过opencv获取实时视频流
        dispW=680
        dispH=480
        flip=2
        camSet2=' tcpclientsrc host=192.168.43.201 port=8554 ! gdpdepay ! rtph264depay ! h264parse ! nvv4l2decoder  ! nvvidconv flip-method='+str(flip)+' ! video/x-raw,format=BGRx ! videoconvert ! video/x-raw, width='+str(dispW)+', height='+str(dispH)+',format=BGR ! appsink  drop=true sync=false '
        self.video = cv2.VideoCapture(camSet2) 
    
    def __del__(self):
        self.video.release()
    
    def get_frame(self):

        # 開啟網路攝影機
        cap = self.video

        # 設定影像尺寸
        width = 1280
        height = 720

        # 設定擷取影像的尺寸大小
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # 計算畫面面積
        area = width * height

        # 初始化平均影像
        ret, frame = cap.read()
        avg = cv2.blur(frame, (4, 4))
        avg_float = np.float32(avg)

        while(cap.isOpened()):
            # 讀取一幅影格
            ret, frame = cap.read()
            
            print(ret)

            if frame is None: 
                print("empty frame")
                break

            # 模糊處理
            blur = cv2.blur(frame, (4, 4))

            # 計算目前影格與平均影像的差異值
            diff = cv2.absdiff(avg, blur)

            # 將圖片轉為灰階
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

            # 篩選出變動程度大於門檻值的區域
            ret, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)

            # 使用型態轉換函數去除雜訊
            kernel = np.ones((5, 5), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

            # 產生等高線
            cnts = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)[0] 

            for c in cnts:
                # 忽略太小的區域
                if cv2.contourArea(c) < 2500:
                    continue

                # 偵測到物體，可以自己加上處理的程式碼在這裡...!!!!!!!!!!!
                #img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = letterbox(frame, 640, 64)[0]
                pred = model(img)
                frame = plot_box(img,pred.xywhn[0])
                
                # 計算等高線的外框範圍
                (x, y, w, h) = cv2.boundingRect(c)

                # 畫出外框
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # 畫出等高線（除錯用）
                cv2.drawContours(frame, cnts, -1, (0, 255, 255), 2)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                # 更新平均影像
                cv2.accumulateWeighted(blur, avg_float, 0.01)
                avg = cv2.convertScaleAbs(avg_float)

                # 因为opencv读取的图片并非jpeg格式，因此要用motion JPEG模式需要先将图片转码成jpg格式图片
                ret, jpeg = cv2.imencode('.jpg', frame)
                return jpeg.tobytes()

app = Flask(__name__)

@app.route('/')  # 主页
def index():
    # jinja2模板，具体格式保存在index.html文件中
    return render_template('index.html')

def gen(camera):
    while True:
        try:
            frame = camera.get_frame()
            # 使用generator函数输出视频流， 每次请求输出的content类型是image/jpeg
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        except:
            print('some thing error')
            pass

@app.route('/video_feed')  # 这个地址返回视频流响应
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')   

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001) 