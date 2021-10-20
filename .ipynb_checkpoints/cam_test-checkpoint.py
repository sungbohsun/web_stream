import cv2

# 選擇第二隻攝影機
camSet2='rtsp://10.96.212.247:5555/unicast'
cap = cv2.VideoCapture(camSet2)
import time

fpsLimit = 1 # throttle limit
startTime = time.time()

while(True):
  # 從攝影機擷取一張影像

    ret, frame = cap.read()
    nowTime = time.time()
    if (int(nowTime - startTime)) > fpsLimit:
        # 顯示圖片
        cv2.imshow('frame', frame)
        startTime = time.time() # reset time


    # 若按下 q 鍵則離開迴圈
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 釋放攝影機
cap.release()

# 關閉所有 OpenCV 視窗
cv2.destroyAllWindows()