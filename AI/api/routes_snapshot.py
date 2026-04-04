import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from core.state import state, state_lock

router = APIRouter()


@router.get("/last_snapshot")
def last_snapshot():
    with state_lock:
        path = state.last_snapshot_path

    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No snapshot found")

    with open(path, "rb") as f:
        data = f.read()

    return Response(content=data, media_type="image/jpeg")
