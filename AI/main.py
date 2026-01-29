import cv2
import numpy as np
from imutils.video import VideoStream
from .yolodetect import YoloDetect

video = VideoStream(src=0).start()
points = []
detect = False

# Đếm điện thoại (COCO: "cell phone")
model = YoloDetect(detect_class="person")


def handle_left_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        param.append([x, y])


def draw_polygon(frame, points):
    for p in points:
        cv2.circle(frame, (p[0], p[1]), 5, (0, 0, 255), -1)

    if len(points) >= 2:
        cv2.polylines(frame, [np.int32(points)], False, (255, 0, 0), 2)

    return frame


cv2.namedWindow("Intrusion Warning")
cv2.setMouseCallback("Intrusion Warning", handle_left_click, points)

while True:
    frame = video.read()
    if frame is None:
        continue

    frame = cv2.flip(frame, 1)
    frame = draw_polygon(frame, points)

    if detect:
        # detect() trả về (frame, stable_count, raw_count)
        frame, stable_count, raw_count = model.detect(frame, points)

        # (tuỳ chọn) in log
        # print("phones:", stable_count, "raw:", raw_count)

    cv2.imshow("Intrusion Warning", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

    # Start detect khi polygon đủ 3 điểm
    elif key == ord('d') and len(points) >= 3:
        # đóng polygon nếu chưa đóng
        if points[0] != points[-1]:
            points.append(points[0])
        detect = True

    # Reset ROI
    elif key == ord('r'):
        points.clear()
        detect = False

video.stop()
cv2.destroyAllWindows()
