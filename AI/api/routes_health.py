from fastapi import APIRouter

from core.config import settings
from core.state import state, state_lock

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "model": settings.model_path,
        "conf": settings.conf_thres,
        "stream_source": settings.stream_source,
        "rtsp_url_configured": bool(settings.rtsp_url),
        "rtsp_transport": settings.rtsp_transport,
        "checkpoint_cx_norm": settings.checkpoint_cx_norm,
        "checkpoint_cy_norm": settings.checkpoint_cy_norm,
        "checkpoint_w_norm": settings.checkpoint_w_norm,
        "checkpoint_h_norm": settings.checkpoint_h_norm,
    }


@router.get("/status")
def status():
    with state_lock:
        return {
            "status": "ok",
            "count": state.count,
            "carry_events": state.carry_events,
            "alarm": state.alarm,
            "latency_ms": state.latency_ms,
            "ts": state.ts,
            "last_events": state.last_events,
            "last_snapshot_path": state.last_snapshot_path,
            "stream_source": state.stream_source,
            "stream_ready": state.stream_ready,
            "stream_error": state.stream_error,
            "stream_frames": state.stream_frames,
            "stream_last_frame_ts": state.stream_last_frame_ts,
        }
