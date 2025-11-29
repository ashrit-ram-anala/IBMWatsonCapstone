"""Main pipeline orchestrator for Watsonx nodes."""
import logging
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import pandas as pd

from app.watsonx.nodes.ingestion_node import IngestionNode
from app.watsonx.nodes.validation_node import ValidationNode
from app.watsonx.nodes.cleaning_node import CleaningNode
from app.watsonx.nodes.anomaly_detector_node import AnomalyDetectorNode

logger = logging.getLogger(__name__)


class DataPipeline:
    def __init__(self):
        self.pipeline_id = str(uuid.uuid4())
        self.nodes = {
            "ingestion": IngestionNode(),
            "validation": ValidationNode(),
            "cleaning": CleaningNode(),
            "anomaly_detection": AnomalyDetectorNode()
        }

    async def execute_full_pipeline(
        self,
        source_type: str,
        source_path: Optional[str] = None,
        connection_string: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        logger.info(f"Starting pipeline execution: {self.pipeline_id}")
        start_time = datetime.utcnow()

        pipeline_results = {
            "pipeline_id": self.pipeline_id,
            "status": "running",
            "stages": {},
            "overall_metrics": {},
            "errors": []
        }

        try:
            logger.info("Stage 1: Data Ingestion")
            ingestion_result = await self.nodes["ingestion"].execute(
                source_type=source_type,
                source_path=source_path,
                connection_string=connection_string,
                api_endpoint=api_endpoint,
                **kwargs
            )

            if not ingestion_result.get("success"):
                pipeline_results["status"] = "failed"
                pipeline_results["errors"].append({
                    "stage": "ingestion",
                    "error": ingestion_result.get("error")
                })
                return pipeline_results

            pipeline_results["stages"]["ingestion"] = {
                "status": "completed",
                "metrics": ingestion_result.get("metadata", {})
            }

            dataframe = ingestion_result["dataframe"]
            logger.info(f"Ingestion complete: {len(dataframe)} rows")

            logger.info("Stage 2: Schema Validation")
            validation_result = await self.nodes["validation"].execute(dataframe=dataframe)

            if not validation_result.get("success"):
                pipeline_results["status"] = "failed"
                pipeline_results["errors"].append({
                    "stage": "validation",
                    "error": validation_result.get("error")
                })
                return pipeline_results

            pipeline_results["stages"]["validation"] = {
                "status": "completed",
                "metrics": validation_result.get("metrics", {})
            }

            dataframe = validation_result["dataframe"]
            logger.info(f"Validation complete: {validation_result['metrics']['valid_rows']} valid rows")

            logger.info("Stage 3: Data Cleaning")
            cleaning_result = await self.nodes["cleaning"].execute(dataframe=dataframe)

            if not cleaning_result.get("success"):
                pipeline_results["status"] = "failed"
                pipeline_results["errors"].append({
                    "stage": "cleaning",
                    "error": cleaning_result.get("error")
                })
                return pipeline_results

            pipeline_results["stages"]["cleaning"] = {
                "status": "completed",
                "metrics": cleaning_result.get("metrics", {})
            }

            dataframe = cleaning_result["dataframe"]
            logger.info(f"Cleaning complete: {cleaning_result['metrics']['rows_modified']} rows modified")

            logger.info("Stage 4: Anomaly Detection")
            anomaly_result = await self.nodes["anomaly_detection"].execute(dataframe=dataframe)

            if not anomaly_result.get("success"):
                pipeline_results["status"] = "failed"
                pipeline_results["errors"].append({
                    "stage": "anomaly_detection",
                    "error": anomaly_result.get("error")
                })
                return pipeline_results

            pipeline_results["stages"]["anomaly_detection"] = {
                "status": "completed",
                "metrics": anomaly_result.get("metrics", {}),
                "anomalies": anomaly_result.get("anomalies", [])
            }

            dataframe = anomaly_result["dataframe"]
            logger.info(f"Anomaly detection complete: {len(anomaly_result.get('anomalies', []))} anomalies found")

            logger.info("Stage 5: Review & Feedback")
            review_metrics = self._compute_review_metrics(
                dataframe,
                ingestion_result,
                validation_result,
                cleaning_result,
                anomaly_result
            )

            pipeline_results["stages"]["review"] = {
                "status": "completed",
                "metrics": review_metrics
            }

            logger.info("Stage 6: Publishing")
            pipeline_results["stages"]["publishing"] = {
                "status": "completed",
                "dataframe": dataframe,
                "rows_published": len(dataframe)
            }

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            pipeline_results["status"] = "completed"
            pipeline_results["overall_metrics"] = {
                "total_rows_ingested": ingestion_result.get("rows_ingested", 0),
                "valid_rows": validation_result["metrics"]["valid_rows"],
                "invalid_rows": validation_result["metrics"]["invalid_rows"],
                "cleaned_rows": cleaning_result["metrics"]["rows_modified"],
                "anomalies_detected": len(anomaly_result.get("anomalies", [])),
                "quality_score": review_metrics.get("quality_score", 0),
                "duration_seconds": round(duration, 2)
            }

            logger.info(f"Pipeline execution completed in {duration:.2f}s")
            return pipeline_results

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            pipeline_results["status"] = "failed"
            pipeline_results["errors"].append({
                "stage": "pipeline",
                "error": str(e)
            })
            return pipeline_results

    def _compute_review_metrics(
        self,
        dataframe: pd.DataFrame,
        ingestion_result: Dict,
        validation_result: Dict,
        cleaning_result: Dict,
        anomaly_result: Dict
    ) -> Dict[str, Any]:
        total_rows = len(dataframe)
        valid_rows = validation_result["metrics"]["valid_rows"]
        anomaly_count = len(anomaly_result.get("anomalies", []))

        validation_score = (valid_rows / total_rows * 100) if total_rows > 0 else 0
        anomaly_penalty = (anomaly_count / total_rows * 100) if total_rows > 0 else 0
        quality_score = max(0, validation_score - anomaly_penalty)

        null_counts = dataframe.isnull().sum()
        total_cells = total_rows * len(dataframe.columns)
        completeness = ((total_cells - null_counts.sum()) / total_cells * 100) if total_cells > 0 else 0

        return {
            "quality_score": round(quality_score, 2),
            "completeness_score": round(completeness, 2),
            "validation_rate": validation_result["metrics"]["validation_rate"],
            "anomaly_rate": anomaly_result["metrics"]["anomaly_rate"],
            "cleaning_rate": cleaning_result["metrics"]["modification_rate"],
            "total_errors": validation_result["metrics"]["error_count"] + anomaly_count,
            "improvement_percentage": round(cleaning_result["metrics"]["modification_rate"], 2)
        }

    def get_pipeline_config(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "pipeline_name": "Banking Data Cleaning Pipeline",
            "nodes": [
                self.nodes["ingestion"].get_node_config(),
                self.nodes["validation"].get_node_config(),
                self.nodes["cleaning"].get_node_config(),
                self.nodes["anomaly_detection"].get_node_config()
            ],
            "execution_order": [
                "ingestion",
                "validation",
                "cleaning",
                "anomaly_detection",
                "review",
                "publishing"
            ]
        }
