from fastapi import APIRouter
from .sbom import router as sbom_router
from .scan import router as scan_router

api_router = APIRouter()
api_router.include_router(sbom_router)
api_router.include_router(scan_router)
