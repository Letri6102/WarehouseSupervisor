import os
import time
import threading
from typing import Optional, Tuple
from urllib.parse import quote
import cv2

from core.config import settings
from core.state import state, state_lock


class StreamManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._frame_cond = threading.Condition(self._lock)
        self._cap: Optional[cv2.VideoCapture] = None
        self._latest_frame = None
        self._latest_frame_ts = 0.0
        self._opened_url = ""
        self._stop = False
        self._worker: Optional[threading.Thread] = None

    @staticmethod
    def _safe_rtsp_url(url: str) -> str:
        if not url.startswith("rtsp://"):
            return url
        prefix = "rtsp://"
        body = url[len(prefix):]
        if "@" not in body:
            return url
        auth, rest = body.split("@", 1)
        if ":" not in auth:
            return url
        user, password = auth.split(":", 1)
        return f"{prefix}{quote(user, safe='')}:{quote(password, safe='')}@{rest}"

    def _set_stream_state(self, ready: bool, error: str = ""):
        with state_lock:
            state.stream_ready = ready
            state.stream_error = error

    def _open_capture(self) -> cv2.VideoCapture:
        if settings.stream_source == "rtsp":
            if not settings.rtsp_url:
                raise RuntimeError("STREAM_SOURCE=rtsp nhưng RTSP_URL đang trống")

            safe_url = self._safe_rtsp_url(settings.rtsp_url)
            self._opened_url = safe_url

            cap = cv2.VideoCapture(safe_url)
            if cap is not None and cap.isOpened():
                time.sleep(settings.stream_open_warmup_sec)
                ok, frame = cap.read()
                if ok and frame is not None:
                    return cap
                cap.release()

            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{settings.rtsp_transport}"
            cap = cv2.VideoCapture(safe_url, cv2.CAP_FFMPEG)
            if cap is not None and cap.isOpened():
                time.sleep(settings.stream_open_warmup_sec)
                ok, frame = cap.read()
                if ok and frame is not None:
                    return cap
                cap.release()

            if settings.rtsp_transport != "udp":
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
                cap = cv2.VideoCapture(safe_url, cv2.CAP_FFMPEG)
                if cap is not None and cap.isOpened():
                    time.sleep(settings.stream_open_warmup_sec)
                    ok, frame = cap.read()
                    if ok and frame is not None:
                        return cap
                    cap.release()

            raise RuntimeError("Không mở được RTSP stream bằng OpenCV")

        cap = cv2.VideoCapture(settings.camera_index)
        if cap is None or not cap.isOpened():
            raise RuntimeError(f"Không mở được webcam index={settings.camera_index}")
        self._opened_url = f"webcam:{settings.camera_index}"
        return cap

    def _release_capture(self):
        with self._lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None

    def _worker_loop(self):
        min_interval = (1.0 / settings.stream_target_fps) if settings.stream_target_fps > 0 else 0.0

        while not self._stop:
            try:
                cap = self._open_capture()
                with self._lock:
                    self._cap = cap
                self._set_stream_state(True, "")
                print(f"[STREAM] opened: {self._opened_url}")

                while not self._stop:
                    t0 = time.time()
                    ok, frame = cap.read()
                    now = time.time()
                    if not ok or frame is None:
                        raise RuntimeError("Đọc frame thất bại")

                    with self._lock:
                        self._latest_frame = frame.copy()
                        self._latest_frame_ts = now
                        self._frame_cond.notify_all()

                    with state_lock:
                        state.stream_frames += 1
                        state.stream_last_frame_ts = now

                    if min_interval > 0:
                        elapsed = time.time() - t0
                        if elapsed < min_interval:
                            time.sleep(min_interval - elapsed)

            except Exception as e:
                self._set_stream_state(False, str(e))
                print(f"[STREAM] error: {e}")
            finally:
                self._release_capture()

            if not self._stop:
                time.sleep(settings.stream_retry_delay_sec)

    def start(self):
        if self._worker and self._worker.is_alive():
            return
        self._stop = False
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def stop(self):
        self._stop = True
        self._release_capture()
        with self._lock:
            self._frame_cond.notify_all()

    def get_frame(self, wait_timeout: float = 3.0) -> Tuple[any, float]:
        deadline = time.time() + wait_timeout
        with self._lock:
            while not self._stop:
                if self._latest_frame is not None:
                    age = time.time() - self._latest_frame_ts
                    if age <= settings.stream_frame_timeout_sec:
                        return self._latest_frame.copy(), self._latest_frame_ts

                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                self._frame_cond.wait(timeout=remaining)
        raise RuntimeError("Không lấy được frame mới từ stream")


stream_manager = StreamManager()
