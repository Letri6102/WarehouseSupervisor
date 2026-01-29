import cv2
import time
import numpy as np
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from pathlib import Path

app = FastAPI()

# Cho phép web gọi status/snapshot (proxy thì không cần, nhưng để an toàn)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = Path(__file__).resolve().parent / "model" / "yolov8n.pt"
model = YOLO(str(MODEL_PATH))
names = model.names

TARGET_LABEL = "person"
TARGET_IDS = {i for i, n in names.items() if n == TARGET_LABEL}

# ✅ macOS: ưu tiên AVFoundation
cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

latest = {"count": 0, "ts": 0.0}

def read_frame():
    ok, frame = cap.read()
    if not ok or frame is None:
        return None
    return frame

def gen_mjpeg():
    global latest
    while True:
        frame = read_frame()
        if frame is None:
            # tạo frame placeholder để bạn thấy ngay là "camera chưa đọc được"
            ph = np.zeros((720, 1280, 3), dtype=np.uint8)
            cv2.putText(ph, "NO CAMERA FRAME", (40, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
            frame = ph
            time.sleep(0.05)

        # YOLO
        results = model.predict(frame, conf=0.35, iou=0.45, imgsz=640, verbose=False)
        r = results[0]

        count = 0
        if r.boxes is not None:
            for b in r.boxes:
                cls_id = int(b.cls.item())
                if TARGET_IDS and cls_id not in TARGET_IDS:
                    continue
                x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
                conf = float(b.conf.item())
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"person {conf:.2f}", (x1, max(20, y1 - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                count += 1

        latest = {"count": count, "ts": time.time()}

        ok, jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n"
               b"Cache-Control: no-cache\r\n\r\n" + jpg.tobytes() + b"\r\n")

@app.get("/video")
def video():
    headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
    return StreamingResponse(gen_mjpeg(), media_type="multipart/x-mixed-replace; boundary=frame", headers=headers)

@app.get("/status")
def status():
    return JSONResponse(latest)

@app.get("/snapshot")
def snapshot():
    frame = read_frame()
    if frame is None:
        return Response(content=b"", media_type="image/jpeg", status_code=500)
    ok, jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        return Response(content=b"", media_type="image/jpeg", status_code=500)
    return Response(content=jpg.tobytes(), media_type="image/jpeg")
