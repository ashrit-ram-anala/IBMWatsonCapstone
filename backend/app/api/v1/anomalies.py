"""Anomaly detection API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import logging

from app.api.v1.ingestion import active_pipelines

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_all_anomalies(
    severity: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get all detected anomalies across all pipelines.

    Args:
        severity: Filter by severity (low, medium, high, critical)
        limit: Maximum number of anomalies to return

    Returns:
        List of anomalies
    """
    all_anomalies = []

    for pipeline_id, pipeline_data in active_pipelines.items():
        result = pipeline_data.get("result", {})
        stages = result.get("stages", {})
        anomaly_stage = stages.get("anomaly_detection", {})
        anomalies = anomaly_stage.get("anomalies", [])

        for anomaly in anomalies:
            anomaly_with_pipeline = anomaly.copy()
            anomaly_with_pipeline["pipeline_id"] = pipeline_id
            all_anomalies.append(anomaly_with_pipeline)

    # Filter by severity if specified
    if severity:
        all_anomalies = [a for a in all_anomalies if a.get("severity") == severity.lower()]

    # Apply limit
    all_anomalies = all_anomalies[:limit]

    return {
        "total": len(all_anomalies),
        "anomalies": all_anomalies
    }


@router.get("/{pipeline_id}")
async def get_pipeline_anomalies(pipeline_id: str) -> Dict[str, Any]:
    """
    Get anomalies detected in a specific pipeline.

    Args:
        pipeline_id: Pipeline ID to query

    Returns:
        List of anomalies for the pipeline
    """
    if pipeline_id not in active_pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")

    pipeline_data = active_pipelines[pipeline_id]
    result = pipeline_data.get("result", {})

    if not result:
        raise HTTPException(status_code=400, detail="Pipeline has not completed yet")

    stages = result.get("stages", {})
    anomaly_stage = stages.get("anomaly_detection", {})
    anomalies = anomaly_stage.get("anomalies", [])

    # Group by severity
    by_severity = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": []
    }

    for anomaly in anomalies:
        severity = anomaly.get("severity", "medium")
        by_severity[severity].append(anomaly)

    # Group by type
    by_type = {}
    for anomaly in anomalies:
        anomaly_type = anomaly.get("anomaly_type", "other")
        if anomaly_type not in by_type:
            by_type[anomaly_type] = []
        by_type[anomaly_type].append(anomaly)

    return {
        "pipeline_id": pipeline_id,
        "total_anomalies": len(anomalies),
        "by_severity": {
            severity: len(items)
            for severity, items in by_severity.items()
        },
        "by_type": {
            anomaly_type: len(items)
            for anomaly_type, items in by_type.items()
        },
        "anomalies": anomalies,
        "grouped": {
            "by_severity": by_severity,
            "by_type": by_type
        }
    }


@router.get("/stats/summary")
async def get_anomaly_summary() -> Dict[str, Any]:
    """
    Get summary statistics for all anomalies.

    Returns:
        Anomaly statistics
    """
    total_anomalies = 0
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    by_type = {}
    by_detector = {}

    for pipeline_data in active_pipelines.values():
        result = pipeline_data.get("result", {})
        stages = result.get("stages", {})
        anomaly_stage = stages.get("anomaly_detection", {})
        anomalies = anomaly_stage.get("anomalies", [])

        total_anomalies += len(anomalies)

        for anomaly in anomalies:
            # Count by severity
            severity = anomaly.get("severity", "medium")
            by_severity[severity] = by_severity.get(severity, 0) + 1

            # Count by type
            anomaly_type = anomaly.get("anomaly_type", "other")
            by_type[anomaly_type] = by_type.get(anomaly_type, 0) + 1

            # Count by detector
            detector = anomaly.get("detected_by", "unknown")
            by_detector[detector] = by_detector.get(detector, 0) + 1

    return {
        "total_anomalies": total_anomalies,
        "by_severity": by_severity,
        "by_type": by_type,
        "by_detector": by_detector
    }
