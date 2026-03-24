import os
import time
import cv2
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from detector.yolo_detector import YOLODetector
from detector.phone_violation import (
    detect_phone_violation,
    PERSON_CLASS_ID,
    PHONE_CLASS_ID,
)
from utils.draw import draw_box
from utils.image_codec import b64_to_bgr_image, bgr_image_to_b64
from zalo_oa import ZaloOANotifier

load_dotenv()


# =========================
# CONFIG
# =========================
APP_NAME = "WarehouseSupervisor-AI"
MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")
CONF_THRES = float(os.getenv("CONF_THRES", "0.4"))
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", "snapshots"))
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

ZALO_OA_ENABLED = os.getenv("ZALO_OA_ENABLED", "false").lower() == "true"
ZALO_OA_ACCESS_TOKEN = os.getenv("ZALO_OA_ACCESS_TOKEN", "")
ZALO_OA_MESSAGE_ENDPOINT = os.getenv(
    "ZALO_OA_MESSAGE_ENDPOINT",
    "https://openapi.zalo.me/v3.0/oa/message/cs",
)
ZALO_OA_RECIPIENTS = [
    x.strip()
    for x in os.getenv("ZALO_OA_RECIPIENTS", "").split(",")
    if x.strip()
]
ZALO_OA_COOLDOWN_SECONDS = int(os.getenv("ZALO_OA_COOLDOWN_SECONDS", "120"))


# =========================
# FASTAPI INIT
# =========================
app = FastAPI(title=APP_NAME, version="1.1.0")
detector: Optional[YOLODetector] = None
zalo_notifier: Optional[ZaloOANotifier] = None


# =========================
# SHARED STATE
# =========================
_state_lock = threading.Lock()
_state = {
    "ts": 0,
    "count": 0,
    "phones": 0,
    "violations": 0,
    "alarm": False,
    "latency_ms": 0,
    "last_snapshot_path": "",
    "last_alert_text": "",
    "last_zalo_result": [],
}
_last_zalo_alert_ts = 0.0


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


class Violation(BaseModel):
    person_bbox: BBox
    person_conf: float
    phone_bbox: BBox
    phone_conf: float


class InferResponse(BaseModel):
    alarm: bool
    violations: List[Violation]
    latency_ms: int
    annotated_b64: Optional[str] = None


# =========================
# HELPERS
# =========================
def annotate_frame(frame, detections, violations):
    vis = frame.copy()

    for det in detections:
        if det["class_id"] == PERSON_CLASS_ID:
            draw_box(vis, det["bbox"], label="PERSON", color=(0, 255, 0))
        elif det["class_id"] == PHONE_CLASS_ID:
            draw_box(vis, det["bbox"], label="PHONE", color=(255, 0, 0))

    for v in violations:
        draw_box(vis, v["person_bbox"], label="VIOLATION_PERSON", color=(0, 0, 255))
        draw_box(vis, v["phone_bbox"], label="VIOLATION_PHONE", color=(0, 0, 255))

    if len(violations) > 0:
        cv2.putText(
            vis,
            "ALARM: PHONE USAGE!",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3,
        )

    return vis


def save_snapshot(frame) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = SNAPSHOT_DIR / f"phone_violation_{ts}.jpg"
    cv2.imwrite(str(out_path), frame)
    return str(out_path)


def build_alert_text(persons: int, phones: int, violations: int, snapshot_path: str) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"[CANH BAO] Phat hien nghi van su dung dien thoai\n"
        f"Thoi gian: {now_str}\n"
        f"So nguoi: {persons}\n"
        f"So dien thoai detect duoc: {phones}\n"
        f"So vi pham: {violations}\n"
        f"Anh luu: {snapshot_path}"
    )


def maybe_send_zalo_alert(annotated_frame, persons: int, phones: int, violations: int):
    global _last_zalo_alert_ts, zalo_notifier

    if violations <= 0:
        return

    if zalo_notifier is None or not zalo_notifier.is_ready():
        return

    now = time.time()
    if now - _last_zalo_alert_ts < ZALO_OA_COOLDOWN_SECONDS:
        return

    snapshot_path = save_snapshot(annotated_frame)
    alert_text = build_alert_text(persons, phones, violations, snapshot_path)
    results = zalo_notifier.send_text_to_many(alert_text)

    _last_zalo_alert_ts = now

    with _state_lock:
        _state["last_snapshot_path"] = snapshot_path
        _state["last_alert_text"] = alert_text
        _state["last_zalo_result"] = results


def update_state(persons: int, phones: int, violations: int, latency_ms: int):
    with _state_lock:
        _state["ts"] = int(time.time())
        _state["count"] = persons
        _state["phones"] = phones
        _state["violations"] = violations
        _state["alarm"] = violations > 0
        _state["latency_ms"] = latency_ms


def process_frame(frame):
    if detector is None:
        raise RuntimeError("Model not ready")

    t0 = time.time()
    detections = detector.detect(frame)
    violations_raw = detect_phone_violation(detections)

    persons = sum(1 for d in detections if d["class_id"] == PERSON_CLASS_ID)
    phones = sum(1 for d in detections if d["class_id"] == PHONE_CLASS_ID)
    latency_ms = int((time.time() - t0) * 1000)

    annotated = annotate_frame(frame, detections, violations_raw)

    update_state(
        persons=persons,
        phones=phones,
        violations=len(violations_raw),
        latency_ms=latency_ms,
    )

    maybe_send_zalo_alert(
        annotated_frame=annotated,
        persons=persons,
        phones=phones,
        violations=len(violations_raw),
    )

    return detections, violations_raw, annotated, latency_ms


# =========================
# STARTUP
# =========================
@app.on_event("startup")
def startup_event():
    global detector, zalo_notifier

    print("Loading YOLO model...")
    detector = YOLODetector(model_path=MODEL_PATH, conf=CONF_THRES)
    print("Model loaded")

    zalo_notifier = ZaloOANotifier(
        access_token=ZALO_OA_ACCESS_TOKEN,
        endpoint=ZALO_OA_MESSAGE_ENDPOINT,
        recipients=ZALO_OA_RECIPIENTS,
        enabled=ZALO_OA_ENABLED,
    )
    print(f"Zalo notifier ready: {zalo_notifier.is_ready()}")


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
            "phones": _state["phones"],
            "violations": _state["violations"],
            "alarm": _state["alarm"],
            "latency_ms": _state["latency_ms"],
            "ts": _state["ts"],
            "last_snapshot_path": _state["last_snapshot_path"],
            "last_alert_text": _state["last_alert_text"],
            "last_zalo_result": _state["last_zalo_result"],
            "zalo_enabled": ZALO_OA_ENABLED,
            "zalo_ready": bool(zalo_notifier and zalo_notifier.is_ready()),
            "zalo_recipients": ZALO_OA_RECIPIENTS,
        }


# =========================
# INFER IMAGE
# =========================
@app.post("/infer", response_model=InferResponse)
def infer(req: InferRequest):
    if detector is None:
        raise HTTPException(status_code=503, detail="Model not ready")

    frame = b64_to_bgr_image(req.image_b64)
    detections, violations_raw, annotated, latency_ms = process_frame(frame)

    annotated_b64 = None
    if req.return_annotated:
        annotated_b64 = bgr_image_to_b64(annotated, ".jpg", req.jpeg_quality)

    violations: List[Violation] = []
    for v in violations_raw:
        violations.append(
            Violation(
                person_bbox=BBox(*v["person_bbox"]),
                person_conf=v["person_conf"],
                phone_bbox=BBox(*v["phone_bbox"]),
                phone_conf=v["phone_conf"],
            )
        )

    return InferResponse(
        alarm=len(violations_raw) > 0,
        violations=violations,
        latency_ms=latency_ms,
        annotated_b64=annotated_b64,
    )


# =========================
# VIDEO STREAM
# =========================
camera = cv2.VideoCapture(CAMERA_INDEX)


def generate_frames():
    while True:
        ret, frame = camera.read()
        if not ret:
            break

        _, _, annotated, _ = process_frame(frame)

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


# =========================
# EXTRA ENDPOINTS
# =========================
@app.get("/test_zalo")
def test_zalo():
    if zalo_notifier is None:
        raise HTTPException(status_code=503, detail="Zalo notifier not initialized")

    text = (
        f"[TEST] Zalo OA hoat dong\n"
        f"Thoi gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"App: {APP_NAME}"
    )

    results = zalo_notifier.send_text_to_many(text)

    return JSONResponse({
        "ok": True,
        "zalo_ready": zalo_notifier.is_ready(),
        "results": results,
    })


@app.get("/last_snapshot")
def last_snapshot():
    with _state_lock:
        path = _state["last_snapshot_path"]

    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No snapshot found")

    with open(path, "rb") as f:
        data = f.read()

    return Response(content=data, media_type="image/jpeg")