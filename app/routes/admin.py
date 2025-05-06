from fastapi import APIRouter, Response, Depends, HTTPException
from app.core.metrics import prometheus_response, json_response
from app.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])

def _auth(token: str):
    if token != getattr(settings, "API_KEY", None):
        raise HTTPException(status_code=403)

@router.get("/metrics")
def metrics(token: str = Depends(_auth)):
    data, content_type = prometheus_response()
    return Response(content=data, media_type=content_type)

@router.get("/stats")
def stats(token: str = Depends(_auth)):
    return json_response()
