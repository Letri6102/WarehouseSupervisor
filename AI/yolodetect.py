import cv2
import datetime
from pathlib import Path
from collections import deque

import numpy as np
from ultralytics import YOLO

from .phone_counter import build_polygon, count_ultralytics_boxes


class YoloDetect:
    def __init__(
        self,
        detect_class="person",          
        model_path="model/yolov8n.pt",
        conf_threshold=0.35,
        iou_threshold=0.45,
        imgsz=960,
        device=None,
        count_only_inside=True,             
        smooth_window=7,
    ):
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.imgsz = imgsz
        self.device = device

        self.count_only_inside = count_only_inside 
        self.count_hist = deque(maxlen=max(3, int(smooth_window)))

        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        self.model = YOLO(str(self.model_path))
        self.names = self.model.names
        self.detect_class_ids = self._resolve_class_ids(detect_class)

        self.last_alert = None
        self.alert_interval = 3  # seconds

    def _resolve_class_ids(self, detect_class):
        if detect_class is None or detect_class == "all":
            return None
        wanted = {detect_class} if isinstance(detect_class, str) else set(detect_class)
        return {i for i, name in self.names.items() if name in wanted}

    def _draw_box(self, img, class_id, x1, y1, x2, y2, inside=True):
        label = self.names.get(class_id, str(class_id))
        color = (0, 255, 0) if inside else (0, 200, 255)

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, label, (x1, max(15, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        cv2.circle(img, (cx, cy), 4, color, -1)

    def detect(self, frame, points):
        results = self.model.predict(
            frame,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )
        r = results[0]

        poly = build_polygon(points)

        raw_count, kept = count_ultralytics_boxes(
            r.boxes,
            class_ids=self.detect_class_ids,
            poly=poly,
            only_inside=self.count_only_inside,
            keep_outside_debug=True
        )

        for d in kept:
            self._draw_box(frame, d["class_id"], d["x1"], d["y1"], d["x2"], d["y2"], inside=d["inside"])

        self.count_hist.append(raw_count)
        stable_count = int(np.median(np.array(self.count_hist))) if len(self.count_hist) else raw_count

        cv2.putText(frame, f"Phones: {stable_count} (raw {raw_count})",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)

        return frame, stable_count, raw_count
