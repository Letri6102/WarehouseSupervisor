from dotenv import load_dotenv
from fastapi import FastAPI

from api.routes_health import router as health_router
from api.routes_infer import router as infer_router
from api.routes_snapshot import router as snapshot_router
from api.routes_stream import router as stream_router
from core.config import settings
from core.dependencies import init_services, shutdown_services

load_dotenv()

app = FastAPI(title=settings.app_name, version=settings.app_version)

@app.on_event("startup")
def on_startup():
    init_services()

@app.on_event("shutdown")
def on_shutdown():
    shutdown_services()

app.include_router(health_router)
app.include_router(infer_router)
app.include_router(stream_router)
app.include_router(snapshot_router)