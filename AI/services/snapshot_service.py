import time
from pathlib import Path
from typing import Optional

import cv2

from core.config import settings
from core.state import state, state_lock


class SnapshotService:
    def __init__(self, snapshot_dir: Path, cooldown_seconds: int):
        self.snapshot_dir = snapshot_dir
        self.cooldown_seconds = cooldown_seconds
        self._last_snapshot_ts = 0.0

    def save_if_needed(self, frame) -> Optional[str]:
        now = time.time()
        if now - self._last_snapshot_ts < self.cooldown_seconds:
            return None

        ts = time.strftime("%Y%m%d_%H%M%S")
        path = self.snapshot_dir / f"carry_alert_{ts}.jpg"
        ok = cv2.imwrite(str(path), frame)
        if not ok:
            return None

        self._last_snapshot_ts = now
        with state_lock:
            state.last_snapshot_path = str(path)
        return str(path)


snapshot_service = SnapshotService(
    snapshot_dir=settings.snapshot_dir,
    cooldown_seconds=settings.snapshot_cooldown_seconds,
)
