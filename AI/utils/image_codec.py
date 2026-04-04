import base64
import cv2
import numpy as np

def b64_to_bgr_image(image_b64: str) -> np.ndarray:
    # Accepts raw base64 OR "data:image/jpeg;base64,...."
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]

    data = base64.b64decode(image_b64)
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image data")
    return img

def bgr_image_to_b64(img, ext: str = ".jpg", quality: int = 85) -> str:
    encode_params = []
    if ext.lower() in [".jpg", ".jpeg"]:
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]

    ok, buf = cv2.imencode(ext, img, encode_params)
    if not ok:
        raise ValueError("Failed to encode image")

    return base64.b64encode(buf.tobytes()).decode("utf-8")
