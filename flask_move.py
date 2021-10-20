
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, Response
import cv2
import numpy as np

class VideoCamera(object):
    def __init__(self):
        # 通过opencv获取实时视频流
        dispW=680
        dispH=480
        flip=2
        #camSet2=' tcpclientsrc host=192.168.43.201 port=8554 ! gdpdepay ! rtph264depay ! h264parse ! nvv4l2decoder  ! nvvidconv flip-method='+str(flip)+' ! video/x-raw,format=BGRx ! videoconvert ! video/x-raw, width='+str(dispW)+', height='+str(dispH)+',format=BGR ! appsink  drop=true sync=false '
        camSet2='rtsp://admin:950793@192.168.43.17:554/live/profile.0'
        self.video = cv2.VideoCapture(camSet2)

    def __del__(self):
        self.video.release()

    def get_frame(self):
        ret, frame = self.video.read()
        avg = cv2.blur(frame, (4, 4))
        avg_float = np.float32(avg)

        while(self.video.isOpened()):
            # 讀取一幅影格
            ret, frame = self.video.read()

            # 若讀取至影片結尾，則跳出
            if ret == False:
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
#                 if cv2.contourArea(c) < 1500:
#                     continue

                # 偵測到物體，可以自己加上處理的程式碼在這裡...

                # 計算等高線的外框範圍
                (x, y, w, h) = cv2.boundingRect(c)

                # 畫出外框
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # 畫出等高線（除錯用）
                cv2.drawContours(frame, cnts, -1, (0, 255, 255), 2)
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
#         try:
        frame = camera.get_frame()
        # 使用generator函数输出视频流， 每次请求输出的content类型是image/jpeg
        yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
#         except:
#             print('some thing error')
#             pass

@app.route('/video_feed')  # 这个地址返回视频流响应
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')   

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)