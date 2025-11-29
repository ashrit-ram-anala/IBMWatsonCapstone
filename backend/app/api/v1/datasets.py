"""Dataset management API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging

from app.api.v1.ingestion import active_pipelines

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def list_datasets() -> Dict[str, Any]:
    datasets = []

    for pipeline_id, pipeline_data in active_pipelines.items():
        result = pipeline_data.get("result", {})
        overall_metrics = result.get("overall_metrics", {})

        datasets.append({
            "pipeline_id": pipeline_id,
            "file_name": pipeline_data.get("file_name", "Unknown"),
            "source_type": pipeline_data.get("source_type", "csv"),
            "status": pipeline_data.get("status", "unknown"),
            "total_rows": overall_metrics.get("total_rows_ingested", 0),
            "valid_rows": overall_metrics.get("valid_rows", 0),
            "quality_score": overall_metrics.get("quality_score", 0),
            "processing_time": overall_metrics.get("duration_seconds", 0)
        })

    return {
        "total": len(datasets),
        "datasets": datasets
    }


@router.get("/{pipeline_id}")
async def get_dataset(pipeline_id: str) -> Dict[str, Any]:
    if pipeline_id not in active_pipelines:
        raise HTTPException(status_code=404, detail=f"Dataset {pipeline_id} not found")

    pipeline_data = active_pipelines[pipeline_id]
    result = pipeline_data.get("result", {})

    return {
        "pipeline_id": pipeline_id,
        "file_name": pipeline_data.get("file_name"),
        "source_type": pipeline_data.get("source_type"),
        "status": pipeline_data.get("status"),
        "overall_metrics": result.get("overall_metrics", {}),
        "stages": result.get("stages", {}),
        "errors": result.get("errors", [])
    }


@router.get("/{pipeline_id}/download")
async def download_cleaned_dataset(pipeline_id: str) -> Dict[str, Any]:
    if pipeline_id not in active_pipelines:
        raise HTTPException(status_code=404, detail=f"Dataset {pipeline_id} not found")

    pipeline_data = active_pipelines[pipeline_id]

    if pipeline_data.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Dataset processing not completed")

    result = pipeline_data.get("result", {})
    publishing_stage = result.get("stages", {}).get("publishing", {})

    return {
        "message": "Dataset ready for download",
        "pipeline_id": pipeline_id,
        "rows": publishing_stage.get("rows_published", 0),
        "download_url": f"/api/v1/datasets/{pipeline_id}/file"
    }
