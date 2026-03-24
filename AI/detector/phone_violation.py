# AI/detector/phone_violation.py

# COCO class ids
PERSON_CLASS_ID = 0
PHONE_CLASS_ID = 67

# ---- TUNABLE PARAMS ----
MIN_PHONE_CONF = 0.25        # lower than person
UPPER_BODY_RATIO = 0.6       # phone must be in upper body
MIN_AREA_RATIO = 0.004       # phone_area / person_area


def _area(box):
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def _center(box):
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2


def phone_in_upper_body(phone_box, person_box):
    """
    Check phone center lies in upper body region of person
    """
    cx, cy = _center(phone_box)

    x1, y1, x2, y2 = person_box
    upper_y = y1 + UPPER_BODY_RATIO * (y2 - y1)

    return (x1 <= cx <= x2) and (y1 <= cy <= upper_y)


def area_ratio(phone_box, person_box):
    return _area(phone_box) / max(_area(person_box), 1)


def detect_phone_violation(detections):
    """
    Input: detections from YOLODetector.detect()
    Output: list of violations:
    {
        person_bbox
        person_conf
        phone_bbox
        phone_conf
    }
    """

    persons = []
    phones = []

    # ---- SPLIT DETECTIONS ----
    for d in detections:
        if d["class_id"] == PERSON_CLASS_ID:
            persons.append(d)

        elif d["class_id"] == PHONE_CLASS_ID and d["conf"] >= MIN_PHONE_CONF:
            phones.append(d)

    violations = []

    # ---- MATCH PHONE ↔ PERSON ----
    for p in persons:
        p_box = p["bbox"]

        for ph in phones:
            ph_box = ph["bbox"]

            # 1️⃣ must be inside upper body
            if not phone_in_upper_body(ph_box, p_box):
                continue

            # 2️⃣ size constraint (filter tiny false phone)
            if area_ratio(ph_box, p_box) < MIN_AREA_RATIO:
                continue

            violations.append({
                "person_bbox": p_box,
                "person_conf": p["conf"],
                "phone_bbox": ph_box,
                "phone_conf": ph["conf"],
            })

    return violations
