import cv2

def draw_box(img, box, label="", color=(0, 255, 0), thickness=2):
    """
    box: (x1, y1, x2, y2)
    color: (B, G, R)
    """
    x1, y1, x2, y2 = map(int, box)

    cv2.rectangle(
        img,
        (x1, y1),
        (x2, y2),
        color,
        thickness
    )

    if label:
        cv2.putText(
            img,
            label,
            (x1, max(0, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )
