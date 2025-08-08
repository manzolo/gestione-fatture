import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Healtcheck"])

@router.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok"}, status_code=200)