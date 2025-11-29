"""Data ingestion API endpoints."""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import Optional
import logging
import os
import uuid

from app.config import settings
from app.watsonx.pipeline import DataPipeline

logger = logging.getLogger(__name__)

router = APIRouter()

active_pipelines = {}


@router.post("/csv")
async def ingest_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_process: bool = True
):
    logger.info(f"Received CSV upload: {file.filename}")

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        file_id = str(uuid.uuid4())
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{file.filename}")

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"Saved file to: {file_path}")

        if auto_process:
            pipeline = DataPipeline()
            pipeline_id = pipeline.pipeline_id

            active_pipelines[pipeline_id] = {
                "status": "running",
                "file_path": file_path,
                "file_name": file.filename
            }

            background_tasks.add_task(
                execute_pipeline_background,
                pipeline,
                "csv",
                file_path,
                pipeline_id
            )

            return {
                "message": "File uploaded and pipeline started",
                "file_id": file_id,
                "file_name": file.filename,
                "file_path": file_path,
                "pipeline_id": pipeline_id,
                "status": "processing"
            }
        else:
            return {
                "message": "File uploaded successfully",
                "file_id": file_id,
                "file_name": file.filename,
                "file_path": file_path,
                "status": "uploaded"
            }

    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/sql")
async def ingest_sql(
    background_tasks: BackgroundTasks,
    connection_string: str,
    query: Optional[str] = None
):
    logger.info("Received SQL ingestion request")

    try:
        pipeline = DataPipeline()
        pipeline_id = pipeline.pipeline_id

        active_pipelines[pipeline_id] = {
            "status": "running",
            "source_type": "sql"
        }

        background_tasks.add_task(
            execute_pipeline_background,
            pipeline,
            "sql",
            None,
            pipeline_id,
            connection_string=connection_string,
            query=query
        )

        return {
            "message": "SQL ingestion started",
            "pipeline_id": pipeline_id,
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"Error starting SQL ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"SQL ingestion failed: {str(e)}")


@router.post("/api")
async def ingest_api(
    background_tasks: BackgroundTasks,
    api_endpoint: str
):
    logger.info(f"Received API ingestion request: {api_endpoint}")

    try:
        pipeline = DataPipeline()
        pipeline_id = pipeline.pipeline_id

        active_pipelines[pipeline_id] = {
            "status": "running",
            "source_type": "api",
            "api_endpoint": api_endpoint
        }

        background_tasks.add_task(
            execute_pipeline_background,
            pipeline,
            "api",
            None,
            pipeline_id,
            api_endpoint=api_endpoint
        )

        return {
            "message": "API ingestion started",
            "pipeline_id": pipeline_id,
            "api_endpoint": api_endpoint,
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"Error starting API ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"API ingestion failed: {str(e)}")


async def execute_pipeline_background(
    pipeline: DataPipeline,
    source_type: str,
    source_path: Optional[str],
    pipeline_id: str,
    **kwargs
):
    try:
        logger.info(f"Starting background pipeline execution: {pipeline_id}")

        result = await pipeline.execute_full_pipeline(
            source_type=source_type,
            source_path=source_path,
            **kwargs
        )

        active_pipelines[pipeline_id] = {
            "status": result.get("status"),
            "result": result,
            "completed": True
        }

        logger.info(f"Pipeline {pipeline_id} completed with status: {result.get('status')}")

    except Exception as e:
        logger.error(f"Pipeline {pipeline_id} failed: {e}", exc_info=True)
        active_pipelines[pipeline_id] = {
            "status": "failed",
            "error": str(e),
            "completed": True
        }
