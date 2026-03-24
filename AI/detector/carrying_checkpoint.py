import time
import math
from typing import Dict, List, Tuple, Any

import cv2
import numpy as np


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def bbox_center(bbox):
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def bbox_wh(bbox):
    x1, y1, x2, y2 = bbox
    return max(1, x2 - x1), max(1, y2 - y1)


class CheckpointCarryGuard:
    """
    Detect nghi vấn 'mang thêm vật' tại checkpoint bằng:
    - person detection
    - background subtraction
    - centroid tracking nhẹ
    - checkpoint zone giữa camera
    """

    def __init__(
        self,
        checkpoint_cx_norm: float = 0.50,
        checkpoint_cy_norm: float = 0.55,
        checkpoint_w_norm: float = 0.58,
        checkpoint_h_norm: float = 0.80,
        min_suspicious_frames: int = 4,
        max_match_dist_px: int = 90,
        track_max_age_sec: float = 1.2,
        bg_history: int = 300,
        bg_var_threshold: int = 32,
        carry_score_threshold: float = 0.55,
    ):
        self.checkpoint_cx_norm = checkpoint_cx_norm
        self.checkpoint_cy_norm = checkpoint_cy_norm
        self.checkpoint_w_norm = checkpoint_w_norm
        self.checkpoint_h_norm = checkpoint_h_norm

        self.min_suspicious_frames = min_suspicious_frames
        self.max_match_dist_px = max_match_dist_px
        self.track_max_age_sec = track_max_age_sec
        self.carry_score_threshold = carry_score_threshold

        self.bg = cv2.createBackgroundSubtractorMOG2(
            history=bg_history,
            varThreshold=bg_var_threshold,
            detectShadows=False,
        )

        self.next_track_id = 1
        self.tracks: Dict[int, Dict[str, Any]] = {}

    def _normalize_bbox(self, bbox):
        if bbox is None:
            return None

        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            return [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])]

        if isinstance(bbox, dict):
            if all(k in bbox for k in ["x1", "y1", "x2", "y2"]):
                return [int(bbox["x1"]), int(bbox["y1"]), int(bbox["x2"]), int(bbox["y2"])]

        return None

    def _is_person(self, det: Dict[str, Any]) -> bool:
        class_name = str(det.get("class_name", det.get("label", det.get("name", "")))).lower().strip()
        class_id = det.get("class_id", None)

        if class_name == "person":
            return True

        # COCO person class thường là 0
        if class_id == 0:
            return True

        return False

    def _extract_persons(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        persons = []
        for d in detections:
            if not isinstance(d, dict):
                continue

            if not self._is_person(d):
                continue

            bbox = self._normalize_bbox(d.get("bbox"))
            if bbox is None:
                continue

            item = dict(d)
            item["bbox"] = bbox
            persons.append(item)
        return persons

    def _cleanup_tracks(self):
        now = time.time()
        remove_ids = []
        for tid, tr in self.tracks.items():
            if now - tr["last_seen"] > self.track_max_age_sec:
                remove_ids.append(tid)

        for tid in remove_ids:
            self.tracks.pop(tid, None)

    def _match_tracks(self, persons: List[Dict[str, Any]]):
        now = time.time()
        matched = []
        used_track_ids = set()

        detections_with_center = []
        for p in persons:
            cx, cy = bbox_center(p["bbox"])
            detections_with_center.append((p, cx, cy))

        for p, cx, cy in detections_with_center:
            best_tid = None
            best_dist = 10**9

            for tid, tr in self.tracks.items():
                if tid in used_track_ids:
                    continue

                dist = math.hypot(cx - tr["cx"], cy - tr["cy"])
                if dist < best_dist and dist <= self.max_match_dist_px:
                    best_dist = dist
                    best_tid = tid

            if best_tid is None:
                tid = self.next_track_id
                self.next_track_id += 1
                self.tracks[tid] = {
                    "track_id": tid,
                    "cx": cx,
                    "cy": cy,
                    "prev_cx": cx,
                    "prev_cy": cy,
                    "bbox": p["bbox"],
                    "last_seen": now,
                    "suspicious_hits": 0,
                    "alerted": False,
                }
                used_track_ids.add(tid)
                matched.append((tid, p))
            else:
                tr = self.tracks[best_tid]
                tr["prev_cx"] = tr["cx"]
                tr["prev_cy"] = tr["cy"]
                tr["cx"] = cx
                tr["cy"] = cy
                tr["bbox"] = p["bbox"]
                tr["last_seen"] = now
                used_track_ids.add(best_tid)
                matched.append((best_tid, p))

        self._cleanup_tracks()
        return matched

    def _build_fgmask(self, frame: np.ndarray) -> np.ndarray:
        fg = self.bg.apply(frame)

        _, fg = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)

        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel_big = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, kernel_small)
        fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel_big)
        fg = cv2.dilate(fg, kernel_small, iterations=1)

        return fg

    def _checkpoint_rect(self, frame_w: int, frame_h: int):
        box_w = int(frame_w * self.checkpoint_w_norm)
        box_h = int(frame_h * self.checkpoint_h_norm)

        cx = int(frame_w * self.checkpoint_cx_norm)
        cy = int(frame_h * self.checkpoint_cy_norm)

        x1 = clamp(cx - box_w // 2, 0, frame_w - 1)
        y1 = clamp(cy - box_h // 2, 0, frame_h - 1)
        x2 = clamp(cx + box_w // 2, 0, frame_w - 1)
        y2 = clamp(cy + box_h // 2, 0, frame_h - 1)

        return x1, y1, x2, y2

    def _person_in_checkpoint(self, cx: int, cy: int, frame_w: int, frame_h: int) -> bool:
        x1, y1, x2, y2 = self._checkpoint_rect(frame_w, frame_h)
        return x1 <= cx <= x2 and y1 <= cy <= y2

    def _carry_score(self, fgmask: np.ndarray, bbox: Tuple[int, int, int, int], frame_shape):
        h, w = frame_shape[:2]
        x1, y1, x2, y2 = bbox
        pw, ph = bbox_wh(bbox)

        # mở rộng ROI xung quanh người để kiểm tra blob "dư ra"
        ex1 = clamp(x1 - int(0.28 * pw), 0, w - 1)
        ex2 = clamp(x2 + int(0.28 * pw), 0, w - 1)
        ey1 = clamp(y1 + int(0.08 * ph), 0, h - 1)
        ey2 = clamp(y1 + int(0.95 * ph), 0, h - 1)

        roi = fgmask[ey1:ey2, ex1:ex2]
        if roi.size == 0:
            return 0.0, {}

        px1 = x1 - ex1
        px2 = x2 - ex1
        py1 = y1 - ey1
        py2 = y2 - ey1

        band_w = max(8, int(0.22 * pw))
        upper_y1 = clamp(int(py1 + 0.10 * ph), 0, roi.shape[0] - 1)
        upper_y2 = clamp(int(py1 + 0.85 * ph), 0, roi.shape[0])

        left_x1 = clamp(px1 - band_w, 0, roi.shape[1] - 1)
        left_x2 = clamp(px1, 0, roi.shape[1])

        right_x1 = clamp(px2, 0, roi.shape[1] - 1)
        right_x2 = clamp(px2 + band_w, 0, roi.shape[1])

        left_band = roi[upper_y1:upper_y2, left_x1:left_x2]
        right_band = roi[upper_y1:upper_y2, right_x1:right_x2]

        left_ratio = float(np.count_nonzero(left_band)) / max(1, left_band.size)
        right_ratio = float(np.count_nonzero(right_band)) / max(1, right_band.size)

        ys, xs = np.where(roi > 0)
        fg_extra_ratio = 0.0
        fg_w_ratio = 1.0
        if len(xs) > 0 and len(ys) > 0:
            fg_x1, fg_x2 = int(xs.min()), int(xs.max())
            fg_y1, fg_y2 = int(ys.min()), int(ys.max())
            fg_w = max(1, fg_x2 - fg_x1 + 1)
            fg_h = max(1, fg_y2 - fg_y1 + 1)

            person_area = max(1, pw * ph)
            fg_area = fg_w * fg_h
            fg_extra_ratio = fg_area / person_area
            fg_w_ratio = fg_w / max(1, pw)

        score = 0.0
        if max(left_ratio, right_ratio) > 0.10:
            score += 0.40
        if (left_ratio + right_ratio) > 0.16:
            score += 0.20
        if fg_w_ratio > 1.18:
            score += 0.20
        if fg_extra_ratio > 1.10:
            score += 0.20

        metrics = {
            "left_ratio": round(left_ratio, 4),
            "right_ratio": round(right_ratio, 4),
            "fg_extra_ratio": round(fg_extra_ratio, 4),
            "fg_w_ratio": round(fg_w_ratio, 4),
        }
        return score, metrics

    def update(self, frame: np.ndarray, detections: List[Dict[str, Any]]):
        annotated = frame.copy()
        h, w = frame.shape[:2]

        cp_x1, cp_y1, cp_x2, cp_y2 = self._checkpoint_rect(w, h)
        fgmask = self._build_fgmask(frame)
        persons = self._extract_persons(detections)
        matched = self._match_tracks(persons)

        events = []
        debug_tracks = []

        # Vẽ checkpoint zone
        cv2.rectangle(annotated, (cp_x1, cp_y1), (cp_x2, cp_y2), (0, 255, 255), 2)
        cv2.putText(
            annotated,
            "CHECKPOINT ZONE",
            (cp_x1, max(30, cp_y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )

        for tid, person in matched:
            tr = self.tracks[tid]
            x1, y1, x2, y2 = person["bbox"]
            cx, cy = tr["cx"], tr["cy"]

            in_checkpoint = self._person_in_checkpoint(cx, cy, w, h)
            score, metrics = self._carry_score(fgmask, person["bbox"], frame.shape)
            suspicious_now = in_checkpoint and score >= self.carry_score_threshold

            if suspicious_now:
                tr["suspicious_hits"] += 1
            else:
                tr["suspicious_hits"] = max(0, tr["suspicious_hits"] - 1)

            if in_checkpoint and tr["suspicious_hits"] >= self.min_suspicious_frames and not tr["alerted"]:
                tr["alerted"] = True
                events.append({
                    "track_id": tid,
                    "bbox": [x1, y1, x2, y2],
                    "score": round(score, 3),
                    "metrics": metrics,
                    "crossed": True,
                })

            color = (0, 255, 0)
            label = f"ID {tid}"

            if in_checkpoint:
                color = (255, 180, 0)
                label = f"ID {tid} checkpoint"

            if suspicious_now:
                color = (0, 140, 255)
                label = f"ID {tid} carrying? {score:.2f}"

            if any(e["track_id"] == tid for e in events):
                color = (0, 0, 255)
                label = f"ALERT ID {tid}"

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                annotated,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

            debug_tracks.append({
                "track_id": tid,
                "bbox": [x1, y1, x2, y2],
                "in_checkpoint": in_checkpoint,
                "suspicious_hits": tr["suspicious_hits"],
                "score": round(score, 3),
                "metrics": metrics,
                "alerted": tr["alerted"],
            })

        if len(events) > 0:
            cv2.putText(
                annotated,
                "ALARM: POSSIBLE THEFT / CARRYING OBJECT",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                3,
            )

        return annotated, events, {
            "events_count": len(events),
            "tracks": debug_tracks,
            "fgmask": fgmask,
        }