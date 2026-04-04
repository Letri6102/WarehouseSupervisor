from fastapi import APIRouter, HTTPException

from core.dependencies import get_inference_service
from schemas.infer import BBox, CarryEvent, InferRequest, InferResponse
from utils.image_codec import b64_to_bgr_image, bgr_image_to_b64

router = APIRouter()


@router.post("/infer", response_model=InferResponse)
def infer(req: InferRequest):
    inference_service = get_inference_service()
    if inference_service is None:
        raise HTTPException(status_code=503, detail="Model not ready")

    frame = b64_to_bgr_image(req.image_b64)
    annotated, events, latency_ms = inference_service.process_frame(frame)

    annotated_b64 = None
    if req.return_annotated:
        annotated_b64 = bgr_image_to_b64(annotated, ".jpg", req.jpeg_quality)

    event_objs = []
    for e in events:
        x1, y1, x2, y2 = e["bbox"]
        event_objs.append(
            CarryEvent(
                track_id=e["track_id"],
                bbox=BBox(x1=x1, y1=y1, x2=x2, y2=y2),
                score=e["score"],
                crossed=e["crossed"],
            )
        )

    return InferResponse(
        alarm=len(events) > 0,
        carry_events=event_objs,
        latency_ms=latency_ms,
        annotated_b64=annotated_b64,
    )
