# import os
# import time
# import cv2
# import threading
# from typing import List, Optional

# from fastapi import FastAPI, HTTPException
# from fastapi.responses import StreamingResponse
# from pydantic import BaseModel, Field

# from detector.yolo_detector import YOLODetector
# from detector.carrying_checkpoint import CheckpointCarryGuard
# from utils.image_codec import b64_to_bgr_image, bgr_image_to_b64


# # =========================
# # CONFIG
# # =========================
# APP_NAME = "WarehouseSupervisor-AI"

# MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")
# CONF_THRES = float(os.getenv("CONF_THRES", "0.4"))
# CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

# EXIT_LINE_X_NORM = float(os.getenv("EXIT_LINE_X_NORM", "0.82"))
# EXIT_DIRECTION = os.getenv("EXIT_DIRECTION", "left_to_right")
# EXIT_BAND_PX = int(os.getenv("EXIT_BAND_PX", "140"))
# CARRY_MIN_SUSPICIOUS_FRAMES = int(os.getenv("CARRY_MIN_SUSPICIOUS_FRAMES", "4"))
# TRACK_MAX_MATCH_PX = int(os.getenv("TRACK_MAX_MATCH_PX", "90"))


# # =========================
# # FASTAPI INIT
# # =========================
# app = FastAPI(title=APP_NAME, version="2.0.0")
# detector: Optional[YOLODetector] = None
# carry_guard: Optional[CheckpointCarryGuard] = None


# # =========================
# # SHARED STATE
# # =========================
# _state_lock = threading.Lock()
# _state = {
#     "ts": 0,
#     "count": 0,
#     "carry_events": 0,
#     "alarm": False,
#     "latency_ms": 0,
#     "last_events": [],
# }


# # =========================
# # SCHEMAS
# # =========================
# class InferRequest(BaseModel):
#     image_b64: str
#     return_annotated: bool = False
#     jpeg_quality: int = Field(default=85, ge=30, le=95)


# class BBox(BaseModel):
#     x1: int
#     y1: int
#     x2: int
#     y2: int


# class CarryEvent(BaseModel):
#     track_id: int
#     bbox: BBox
#     score: float
#     crossed: bool


# class InferResponse(BaseModel):
#     alarm: bool
#     carry_events: List[CarryEvent]
#     latency_ms: int
#     annotated_b64: Optional[str] = None


# # =========================
# # STARTUP
# # =========================
# @app.on_event("startup")
# def startup_event():
#     global detector, carry_guard

#     print("Loading YOLO model...")
#     detector = YOLODetector(model_path=MODEL_PATH, conf=CONF_THRES)
#     print("Model loaded")

#     carry_guard = CheckpointCarryGuard(
#         exit_line_x_norm=EXIT_LINE_X_NORM,
#         direction=EXIT_DIRECTION,
#         exit_band_px=EXIT_BAND_PX,
#         min_suspicious_frames=CARRY_MIN_SUSPICIOUS_FRAMES,
#         max_match_dist_px=TRACK_MAX_MATCH_PX,
#     )
#     print("Checkpoint carry guard ready")


# # =========================
# # HEALTH
# # =========================
# @app.get("/health")
# def health():
#     return {
#         "status": "ok",
#         "app": APP_NAME,
#         "model": MODEL_PATH,
#         "conf": CONF_THRES,
#         "exit_line_x_norm": EXIT_LINE_X_NORM,
#         "exit_direction": EXIT_DIRECTION,
#     }


# # =========================
# # STATUS
# # =========================
# @app.get("/status")
# def status():
#     with _state_lock:
#         return {
#             "status": "ok",
#             "count": _state["count"],
#             "carry_events": _state["carry_events"],
#             "alarm": _state["alarm"],
#             "latency_ms": _state["latency_ms"],
#             "ts": _state["ts"],
#             "last_events": _state["last_events"],
#         }


# # =========================
# # CORE PROCESS
# # =========================
# def process_frame(frame):
#     if detector is None or carry_guard is None:
#         raise RuntimeError("Model/guard not ready")

#     t0 = time.time()

#     detections = detector.detect(frame)
#     persons = [d for d in detections if (d.get("class_name") or d.get("label") or "") == "person"]

#     annotated, events, debug = carry_guard.update(frame, detections)

#     latency_ms = int((time.time() - t0) * 1000)

#     with _state_lock:
#         _state["ts"] = int(time.time())
#         _state["count"] = len(persons)
#         _state["carry_events"] = len(events)
#         _state["alarm"] = len(events) > 0
#         _state["latency_ms"] = latency_ms
#         _state["last_events"] = events

#     return annotated, events, latency_ms


# # =========================
# # INFER IMAGE
# # =========================
# @app.post("/infer", response_model=InferResponse)
# def infer(req: InferRequest):
#     frame = b64_to_bgr_image(req.image_b64)

#     annotated, events, latency_ms = process_frame(frame)

#     annotated_b64 = None
#     if req.return_annotated:
#         annotated_b64 = bgr_image_to_b64(annotated, ".jpg", req.jpeg_quality)

#     event_objs = []
#     for e in events:
#         x1, y1, x2, y2 = e["bbox"]
#         event_objs.append(
#             CarryEvent(
#                 track_id=e["track_id"],
#                 bbox=BBox(x1=x1, y1=y1, x2=x2, y2=y2),
#                 score=e["score"],
#                 crossed=e["crossed"],
#             )
#         )

#     return InferResponse(
#         alarm=len(events) > 0,
#         carry_events=event_objs,
#         latency_ms=latency_ms,
#         annotated_b64=annotated_b64,
#     )


# # =========================
# # VIDEO STREAM
# # =========================
# camera = cv2.VideoCapture(CAMERA_INDEX)


# def generate_frames():
#     while True:
#         ret, frame = camera.read()
#         if not ret:
#             break

#         annotated, _, _ = process_frame(frame)

#         ok, buffer = cv2.imencode(".jpg", annotated)
#         if not ok:
#             continue

#         yield (
#             b"--frame\r\n"
#             b"Content-Type: image/jpeg\r\n\r\n"
#             + buffer.tobytes()
#             + b"\r\n"
#         )


# @app.get("/video")
# def video_feed():
#     return StreamingResponse(
#         generate_frames(),
#         media_type="multipart/x-mixed-replace; boundary=frame",
#     )

import os
import time
import cv2
import threading
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field

from detector.yolo_detector import YOLODetector
from detector.carrying_checkpoint import CheckpointCarryGuard
from utils.image_codec import b64_to_bgr_image, bgr_image_to_b64

load_dotenv()


# =========================
# CONFIG
# =========================
APP_NAME = "WarehouseSupervisor-AI"
MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")
CONF_THRES = float(os.getenv("CONF_THRES", "0.4"))
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

CHECKPOINT_CX_NORM = float(os.getenv("CHECKPOINT_CX_NORM", "0.50"))
CHECKPOINT_CY_NORM = float(os.getenv("CHECKPOINT_CY_NORM", "0.55"))
CHECKPOINT_W_NORM = float(os.getenv("CHECKPOINT_W_NORM", "0.58"))
CHECKPOINT_H_NORM = float(os.getenv("CHECKPOINT_H_NORM", "0.80"))

CARRY_MIN_SUSPICIOUS_FRAMES = int(os.getenv("CARRY_MIN_SUSPICIOUS_FRAMES", "4"))
TRACK_MAX_MATCH_PX = int(os.getenv("TRACK_MAX_MATCH_PX", "90"))
TRACK_MAX_AGE_SEC = float(os.getenv("TRACK_MAX_AGE_SEC", "1.2"))
BG_HISTORY = int(os.getenv("BG_HISTORY", "300"))
BG_VAR_THRESHOLD = int(os.getenv("BG_VAR_THRESHOLD", "32"))
CARRY_SCORE_THRESHOLD = float(os.getenv("CARRY_SCORE_THRESHOLD", "0.55"))

SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", "snapshots"))
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOT_COOLDOWN_SECONDS = int(os.getenv("SNAPSHOT_COOLDOWN_SECONDS", "10"))


# =========================
# FASTAPI INIT
# =========================
app = FastAPI(title=APP_NAME, version="2.1.0")
detector: Optional[YOLODetector] = None
carry_guard: Optional[CheckpointCarryGuard] = None


# =========================
# SHARED STATE
# =========================
_state_lock = threading.Lock()
_state = {
    "ts": 0,
    "count": 0,
    "carry_events": 0,
    "alarm": False,
    "latency_ms": 0,
    "last_events": [],
    "last_snapshot_path": "",
}
_last_snapshot_ts = 0.0


# =========================
# SCHEMAS
# =========================
class InferRequest(BaseModel):
    image_b64: str
    return_annotated: bool = False
    jpeg_quality: int = Field(default=85, ge=30, le=95)


class BBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class CarryEvent(BaseModel):
    track_id: int
    bbox: BBox
    score: float
    crossed: bool


class InferResponse(BaseModel):
    alarm: bool
    carry_events: List[CarryEvent]
    latency_ms: int
    annotated_b64: Optional[str] = None


# =========================
# HELPERS
# =========================
def open_camera(index: int):
    # macOS
    cap = cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
    if cap is not None and cap.isOpened():
        return cap

    # Windows / Linux fallback
    cap = cv2.VideoCapture(index)
    return cap


def save_snapshot(frame):
    global _last_snapshot_ts

    now = time.time()
    if now - _last_snapshot_ts < SNAPSHOT_COOLDOWN_SECONDS:
        return None

    ts = time.strftime("%Y%m%d_%H%M%S")
    path = SNAPSHOT_DIR / f"carry_alert_{ts}.jpg"
    ok = cv2.imwrite(str(path), frame)
    if ok:
        _last_snapshot_ts = now
        with _state_lock:
            _state["last_snapshot_path"] = str(path)
        return str(path)

    return None


def process_frame(frame):
    if detector is None or carry_guard is None:
        raise RuntimeError("Model/guard not ready")

    t0 = time.time()

    detections = detector.detect(frame)
    annotated, events, _debug = carry_guard.update(frame, detections)

    # Đếm person tương thích nhiều kiểu output
    person_count = 0
    for d in detections:
        class_name = str(d.get("class_name", d.get("label", d.get("name", "")))).lower().strip()
        class_id = d.get("class_id", None)
        if class_name == "person" or class_id == 0:
            person_count += 1

    latency_ms = int((time.time() - t0) * 1000)

    if len(events) > 0:
        save_snapshot(annotated)

    with _state_lock:
        _state["ts"] = int(time.time())
        _state["count"] = person_count
        _state["carry_events"] = len(events)
        _state["alarm"] = len(events) > 0
        _state["latency_ms"] = latency_ms
        _state["last_events"] = events

    return annotated, events, latency_ms


# =========================
# STARTUP
# =========================
@app.on_event("startup")
def startup_event():
    global detector, carry_guard

    print("Loading YOLO model...")
    detector = YOLODetector(model_path=MODEL_PATH, conf=CONF_THRES)
    print("Model loaded")

    carry_guard = CheckpointCarryGuard(
        checkpoint_cx_norm=CHECKPOINT_CX_NORM,
        checkpoint_cy_norm=CHECKPOINT_CY_NORM,
        checkpoint_w_norm=CHECKPOINT_W_NORM,
        checkpoint_h_norm=CHECKPOINT_H_NORM,
        min_suspicious_frames=CARRY_MIN_SUSPICIOUS_FRAMES,
        max_match_dist_px=TRACK_MAX_MATCH_PX,
        track_max_age_sec=TRACK_MAX_AGE_SEC,
        bg_history=BG_HISTORY,
        bg_var_threshold=BG_VAR_THRESHOLD,
        carry_score_threshold=CARRY_SCORE_THRESHOLD,
    )
    print("Checkpoint carry guard ready")


# =========================
# HEALTH
# =========================
@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": APP_NAME,
        "model": MODEL_PATH,
        "conf": CONF_THRES,
        "checkpoint_cx_norm": CHECKPOINT_CX_NORM,
        "checkpoint_cy_norm": CHECKPOINT_CY_NORM,
        "checkpoint_w_norm": CHECKPOINT_W_NORM,
        "checkpoint_h_norm": CHECKPOINT_H_NORM,
    }


# =========================
# STATUS
# =========================
@app.get("/status")
def status():
    with _state_lock:
        return {
            "status": "ok",
            "count": _state["count"],
            "carry_events": _state["carry_events"],
            "alarm": _state["alarm"],
            "latency_ms": _state["latency_ms"],
            "ts": _state["ts"],
            "last_events": _state["last_events"],
            "last_snapshot_path": _state["last_snapshot_path"],
        }


# =========================
# INFER IMAGE
# =========================
@app.post("/infer", response_model=InferResponse)
def infer(req: InferRequest):
    if detector is None or carry_guard is None:
        raise HTTPException(status_code=503, detail="Model not ready")

    frame = b64_to_bgr_image(req.image_b64)
    annotated, events, latency_ms = process_frame(frame)

    annotated_b64 = None
    if req.return_annotated:
        annotated_b64 = bgr_image_to_b64(annotated, ".jpg", req.jpeg_quality)

    event_objs = []
    for e in events:
        x1, y1, x2, y2 = e["bbox"]
        event_objs.append(
            CarryEvent(
                track_id=e["track_id"],
                bbox=BBox(x1=x1, y1=y1, x2=x2, y2=y2),
                score=e["score"],
                crossed=e["crossed"],
            )
        )

    return InferResponse(
        alarm=len(events) > 0,
        carry_events=event_objs,
        latency_ms=latency_ms,
        annotated_b64=annotated_b64,
    )


# =========================
# VIDEO STREAM
# =========================
camera = open_camera(CAMERA_INDEX)


def generate_frames():
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        annotated, _, _ = process_frame(frame)

        ok, buffer = cv2.imencode(".jpg", annotated)
        if not ok:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )


@app.get("/video")
def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/last_snapshot")
def last_snapshot():
    with _state_lock:
        path = _state["last_snapshot_path"]

    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No snapshot found")

    with open(path, "rb") as f:
        data = f.read()

    return Response(content=data, media_type="image/jpeg")