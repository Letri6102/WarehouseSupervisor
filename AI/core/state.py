import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class RuntimeState:
    ts: int = 0
    count: int = 0
    carry_events: int = 0
    alarm: bool = False
    latency_ms: int = 0
    last_events: List[Dict[str, Any]] = field(default_factory=list)
    last_snapshot_path: str = ""
    stream_source: str = ""
    stream_ready: bool = False
    stream_error: str = ""
    stream_frames: int = 0
    stream_last_frame_ts: float = 0.0


state_lock = threading.Lock()
state = RuntimeState()
