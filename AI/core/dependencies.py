from typing import Optional

from detector.carrying_checkpoint import CheckpointCarryGuard
from detector.yolo_detector import YOLODetector
from core.config import settings
from core.state import state, state_lock
from services.inference_service import InferenceService
from services.stream_manager import stream_manager


detector: Optional[YOLODetector] = None
carry_guard: Optional[CheckpointCarryGuard] = None
_inference_service: Optional[InferenceService] = None


def get_inference_service() -> Optional[InferenceService]:
    return _inference_service


def init_services():
    global detector, carry_guard, _inference_service

    print("Loading YOLO model...")
    detector = YOLODetector(model_path=settings.model_path, conf=settings.conf_thres)
    print("Model loaded")

    carry_guard = CheckpointCarryGuard(
        checkpoint_cx_norm=settings.checkpoint_cx_norm,
        checkpoint_cy_norm=settings.checkpoint_cy_norm,
        checkpoint_w_norm=settings.checkpoint_w_norm,
        checkpoint_h_norm=settings.checkpoint_h_norm,
        min_suspicious_frames=settings.carry_min_suspicious_frames,
        max_match_dist_px=settings.track_max_match_px,
        track_max_age_sec=settings.track_max_age_sec,
        bg_history=settings.bg_history,
        bg_var_threshold=settings.bg_var_threshold,
        carry_score_threshold=settings.carry_score_threshold,
    )
    print("Checkpoint carry guard ready")

    _inference_service = InferenceService(detector=detector, carry_guard=carry_guard)

    with state_lock:
        state.stream_source = settings.stream_source

    stream_manager.start()
    print(f"Stream manager started: source={settings.stream_source}")


def shutdown_services():
    stream_manager.stop()
