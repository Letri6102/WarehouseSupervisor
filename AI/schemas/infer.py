from typing import List, Optional
from pydantic import BaseModel, Field


class InferRequest(BaseModel):
    image_b64: str
    return_annotated: bool = False
    jpeg_quality: int = Field(default=85, ge=30, le=95)


class BBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class CarryEvent(BaseModel):
    track_id: int
    bbox: BBox
    score: float
    crossed: bool


class InferResponse(BaseModel):
    alarm: bool
    carry_events: List[CarryEvent]
    latency_ms: int
    annotated_b64: Optional[str] = None
