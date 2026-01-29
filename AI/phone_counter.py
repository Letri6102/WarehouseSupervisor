# phone_counter.py
from shapely.geometry import Point, Polygon

def build_polygon(points):
    if not points or len(points) < 3:
        return None
    try:
        return Polygon(points)
    except Exception:
        return None

def point_inside(poly, xy):
    if poly is None:
        return True
    return poly.contains(Point(xy))

def count_ultralytics_boxes(boxes, class_ids=None, poly=None, only_inside=True, keep_outside_debug=True):
    if boxes is None:
        return 0, []

    raw_count = 0
    kept = []

    for box in boxes:
        class_id = int(box.cls.item())
        if class_ids is not None and class_id not in class_ids:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        inside = point_inside(poly, (cx, cy))

        if only_inside and not inside:
            if keep_outside_debug:
                kept.append({"class_id": class_id, "x1": x1, "y1": y1, "x2": x2, "y2": y2, "inside": False})
            continue

        raw_count += 1
        kept.append({"class_id": class_id, "x1": x1, "y1": y1, "x2": x2, "y2": y2, "inside": inside})

    return raw_count, kept
