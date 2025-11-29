"""Pipeline management API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from app.api.v1.ingestion import active_pipelines

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str) -> Dict[str, Any]:
    if pipeline_id not in active_pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")

    pipeline_data = active_pipelines[pipeline_id]

    return {
        "pipeline_id": pipeline_id,
        "status": pipeline_data.get("status"),
        "completed": pipeline_data.get("completed", False),
        "result": pipeline_data.get("result"),
        "error": pipeline_data.get("error")
    }


@router.get("/")
async def list_pipelines() -> Dict[str, Any]:
    pipelines = []

    for pipeline_id, data in active_pipelines.items():
        pipelines.append({
            "pipeline_id": pipeline_id,
            "status": data.get("status"),
            "completed": data.get("completed", False),
            "file_name": data.get("file_name"),
            "source_type": data.get("source_type")
        })

    return {
        "total": len(pipelines),
        "pipelines": pipelines
    }


@router.delete("/{pipeline_id}")
async def delete_pipeline(pipeline_id: str) -> Dict[str, Any]:
    if pipeline_id not in active_pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")

    del active_pipelines[pipeline_id]

    return {
        "message": "Pipeline deleted successfully",
        "pipeline_id": pipeline_id
    }
