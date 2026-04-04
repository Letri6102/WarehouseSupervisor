# import os
# import cv2

# PASSWORD = "L265BAE9"
import os
import cv2

# RTSP qua TCP thường ổn định hơn
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

RTSP_URL = "rtsp://admin:Password@192.168.1.71:554/cam/realmonitor?channel=1&subtype=1"

cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("Không mở được camera.")
    exit(1)

print("Đã kết nối. Nhấn q để thoát.")

while True:
    ok, frame = cap.read()
    if not ok or frame is None:
        print("Không đọc được frame.")
        break

    cv2.imshow("Imou 192.168.1.71", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()