from pathlib import Path
import os
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    app_name: str = "WarehouseSupervisor-AI"
    app_version: str = "4.0.0"

    model_path: str = os.getenv("MODEL_PATH", "yolov8n.pt")
    conf_thres: float = float(os.getenv("CONF_THRES", "0.4"))

    stream_source: str = os.getenv("STREAM_SOURCE", "rtsp").strip().lower()
    camera_index: int = int(os.getenv("CAMERA_INDEX", "0"))
    rtsp_url: str = os.getenv("RTSP_URL", "").strip()
    rtsp_transport: str = os.getenv("RTSP_TRANSPORT", "tcp").strip().lower()

    frame_jpeg_quality: int = int(os.getenv("FRAME_JPEG_QUALITY", "85"))
    stream_target_fps: float = float(os.getenv("STREAM_TARGET_FPS", "0"))

    stream_open_warmup_sec: float = float(os.getenv("STREAM_OPEN_WARMUP_SEC", "0.5"))
    stream_retry_delay_sec: float = float(os.getenv("STREAM_RETRY_DELAY_SEC", "2.0"))
    stream_frame_timeout_sec: float = float(os.getenv("STREAM_FRAME_TIMEOUT_SEC", "3.0"))

    snapshot_dir: Path = BASE_DIR / os.getenv("SNAPSHOT_DIR", "snapshots")
    snapshot_cooldown_seconds: int = int(os.getenv("SNAPSHOT_COOLDOWN_SECONDS", "10"))

    checkpoint_cx_norm: float = float(os.getenv("CHECKPOINT_CX_NORM", "0.5"))
    checkpoint_cy_norm: float = float(os.getenv("CHECKPOINT_CY_NORM", "0.5"))
    checkpoint_w_norm: float = float(os.getenv("CHECKPOINT_W_NORM", "0.2"))
    checkpoint_h_norm: float = float(os.getenv("CHECKPOINT_H_NORM", "0.2"))

    carry_min_suspicious_frames: int = int(os.getenv("CARRY_MIN_SUSPICIOUS_FRAMES", "3"))
    track_max_match_px: float = float(os.getenv("TRACK_MAX_MATCH_PX", "120"))
    track_max_age_sec: float = float(os.getenv("TRACK_MAX_AGE_SEC", "1.5"))
    bg_history: int = int(os.getenv("BG_HISTORY", "300"))
    bg_var_threshold: float = float(os.getenv("BG_VAR_THRESHOLD", "16"))
    carry_score_threshold: float = float(os.getenv("CARRY_SCORE_THRESHOLD", "0.55"))

settings = Settings()
settings.snapshot_dir.mkdir(parents=True, exist_ok=True)