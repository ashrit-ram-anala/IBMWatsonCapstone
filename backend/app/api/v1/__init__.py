"""API v1 router."""
from fastapi import APIRouter

from app.api.v1 import ingestion, pipelines, metrics, datasets, anomalies

router = APIRouter()

# Include sub-routers
router.include_router(ingestion.router, prefix="/ingest", tags=["ingestion"])
router.include_router(pipelines.router, prefix="/pipelines", tags=["pipelines"])
router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
