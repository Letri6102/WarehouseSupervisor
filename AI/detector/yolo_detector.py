# AI/detector/yolo_detector.py

from ultralytics import YOLO


class YOLODetector:
    def __init__(
        self,
        model_path="model/yolo26m.pt",
        conf=0.4,
        imgsz=960,
        device=None,
    ):
        """
        model_path : yolov8 / yolo26 model
        conf       : global confidence threshold
        imgsz      : larger helps small objects (phones)
        """
        self.model = YOLO(model_path)
        self.conf = conf
        self.imgsz = imgsz
        self.device = device

    def detect(self, frame):
        """
        Return detections as list of dict:
        {
            class_id: int
            conf: float
            bbox: [x1, y1, x2, y2]
        }
        """
        results = self.model(
            frame,
            conf=self.conf,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )[0]

        detections = []

        if results.boxes is None:
            return detections

        boxes = results.boxes.xyxy.cpu().numpy()
        confs = results.boxes.conf.cpu().numpy()
        clss = results.boxes.cls.cpu().numpy()

        for box, conf, cls_id in zip(boxes, confs, clss):
            x1, y1, x2, y2 = box.astype(int)

            detections.append({
                "class_id": int(cls_id),
                "conf": float(conf),
                "bbox": [x1, y1, x2, y2],
            })

        return detections
