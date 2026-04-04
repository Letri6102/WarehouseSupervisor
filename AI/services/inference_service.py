import time
from typing import Any, Dict, List, Tuple

from core.state import state, state_lock
from services.snapshot_service import snapshot_service


class InferenceService:
    def __init__(self, detector, carry_guard):
        self.detector = detector
        self.carry_guard = carry_guard

    def process_frame(self, frame) -> Tuple[Any, List[dict], int]:
        t0 = time.time()
        detections = self.detector.detect(frame)
        annotated, events, _debug = self.carry_guard.update(frame, detections)

        person_count = 0
        for d in detections:
            class_name = str(d.get("class_name", d.get("label", d.get("name", "")))).lower().strip()
            class_id = d.get("class_id", None)
            if class_name == "person" or class_id == 0:
                person_count += 1

        latency_ms = int((time.time() - t0) * 1000)

        if events:
            snapshot_service.save_if_needed(annotated)

        with state_lock:
            state.ts = int(time.time())
            state.count = person_count
            state.carry_events = len(events)
            state.alarm = len(events) > 0
            state.latency_ms = latency_ms
            state.last_events = events

        return annotated, events, latency_ms
