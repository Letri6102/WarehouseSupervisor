import cv2
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from core.config import settings
from core.dependencies import get_inference_service
from services.stream_manager import stream_manager

router = APIRouter()


def make_error_frame(message: str, width: int = 960, height: int = 540):
    frame = 255 * (cv2.UMat(height, width, cv2.CV_8UC3).get())
    lines = ["RTSP stream error", message[:90], "Dang thu reconnect..."]
    y = 80
    for i, line in enumerate(lines):
        scale = 1.0 if i == 0 else 0.8
        thickness = 2 if i == 0 else 1
        cv2.putText(frame, line, (40, y), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 255), thickness, cv2.LINE_AA)
        y += 50
    return frame


def generate_frames():
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), settings.frame_jpeg_quality]

    while True:
        try:
            frame, _ts = stream_manager.get_frame(wait_timeout=5.0)
            inference_service = get_inference_service()
            if inference_service is None:
                raise RuntimeError("Model not ready")
            annotated, _, _ = inference_service.process_frame(frame)
        except Exception as e:
            annotated = make_error_frame(str(e))

        ok, buffer = cv2.imencode(".jpg", annotated, encode_params)
        if not ok:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


@router.get("/video")
def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"},
    )
