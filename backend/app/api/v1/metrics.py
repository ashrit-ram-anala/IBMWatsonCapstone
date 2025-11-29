"""Metrics and statistics API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.api.v1.ingestion import active_pipelines

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_overall_metrics() -> Dict[str, Any]:
    total_pipelines = len(active_pipelines)
    completed = sum(1 for p in active_pipelines.values() if p.get("completed"))
    failed = sum(1 for p in active_pipelines.values() if p.get("status") == "failed")
    running = sum(1 for p in active_pipelines.values() if p.get("status") == "running")

    total_rows_processed = 0
    total_anomalies = 0
    total_cleaned = 0

    for pipeline_data in active_pipelines.values():
        result = pipeline_data.get("result", {})
        overall_metrics = result.get("overall_metrics", {})

        total_rows_processed += overall_metrics.get("total_rows_ingested", 0)
        total_anomalies += overall_metrics.get("anomalies_detected", 0)
        total_cleaned += overall_metrics.get("cleaned_rows", 0)

    return {
        "total_pipelines": total_pipelines,
        "completed_pipelines": completed,
        "failed_pipelines": failed,
        "running_pipelines": running,
        "total_rows_processed": total_rows_processed,
        "total_anomalies_detected": total_anomalies,
        "total_rows_cleaned": total_cleaned,
        "success_rate": round((completed / total_pipelines * 100) if total_pipelines > 0 else 0, 2)
    }


@router.get("/{pipeline_id}")
async def get_pipeline_metrics(pipeline_id: str) -> Dict[str, Any]:
    if pipeline_id not in active_pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")

    pipeline_data = active_pipelines[pipeline_id]
    result = pipeline_data.get("result", {})

    if not result:
        raise HTTPException(status_code=400, detail="Pipeline has not completed yet")

    return {
        "pipeline_id": pipeline_id,
        "overall_metrics": result.get("overall_metrics", {}),
        "stage_metrics": {
            stage_name: stage_data.get("metrics", {})
            for stage_name, stage_data in result.get("stages", {}).items()
        }
    }
