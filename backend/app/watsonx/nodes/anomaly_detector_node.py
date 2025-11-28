"""Anomaly Detector Node - Uses ML/LLM to detect inconsistent entries."""
import pandas as pd
import logging
from typing import Dict, Any, List
import asyncio

from app.watsonx.client import watsonx_client

logger = logging.getLogger(__name__)


class AnomalyDetectorNode:
    """
    Node 4: Anomaly Detector
    Uses fine-tuned model or zero-shot LLM to detect inconsistent entries.
    """

    def __init__(self, confidence_threshold: float = 0.75):
        self.node_id = "anomaly_detector_node"
        self.node_name = "Anomaly Detector Node"
        self.confidence_threshold = confidence_threshold

    async def execute(self, dataframe: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Execute the anomaly detection node.

        Args:
            dataframe: Input dataframe to analyze

        Returns:
            Dictionary with anomaly detection results
        """
        logger.info(f"Starting anomaly detection for {len(dataframe)} rows")

        df = dataframe.copy()
        anomalies_detected = []
        df['is_anomaly'] = False

        # Rule-based anomaly detection
        rule_based_anomalies = await self._rule_based_detection(df)
        anomalies_detected.extend(rule_based_anomalies)

        # LLM-based anomaly detection (sample subset for efficiency)
        sample_size = min(100, len(df))
        sample_indices = df.sample(n=sample_size, random_state=42).index

        llm_tasks = []
        for idx in sample_indices:
            row = df.loc[idx]
            transaction_data = row.to_dict()
            llm_tasks.append(self._llm_detection(idx, transaction_data))

        # Run LLM detection in batches
        llm_results = await asyncio.gather(*llm_tasks, return_exceptions=True)

        for result in llm_results:
            if isinstance(result, dict) and result.get('is_anomaly'):
                anomalies_detected.append(result)
                idx = result.get('row_index')
                if idx is not None:
                    df.at[idx, 'is_anomaly'] = True

        # Mark all detected anomalies
        for anomaly in rule_based_anomalies:
            idx = anomaly.get('row_index')
            if idx is not None:
                df.at[idx, 'is_anomaly'] = True

        result = {
            "success": True,
            "node_id": self.node_id,
            "dataframe": df,
            "metrics": {
                "total_rows": len(df),
                "anomalies_detected": len(anomalies_detected),
                "anomaly_rate": round(len(anomalies_detected) / len(df) * 100, 2) if len(df) > 0 else 0,
                "rule_based_count": len(rule_based_anomalies),
                "llm_detected_count": len([a for a in anomalies_detected if a.get('detected_by') == 'watsonx-llm'])
            },
            "anomalies": anomalies_detected
        }

        logger.info(f"Anomaly detection complete: {len(anomalies_detected)} anomalies found")
        return result

    async def _rule_based_detection(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Perform rule-based anomaly detection."""
        anomalies = []

        for idx, row in df.iterrows():
            # Rule 1: Negative balance with completed status
            if (pd.notna(row.get('balance')) and
                float(row.get('balance', 0)) < 0 and
                str(row.get('status', '')).lower() == 'completed'):
                anomalies.append({
                    "row_index": idx,
                    "transaction_id": row.get('transaction_id'),
                    "anomaly_type": "negative_balance",
                    "severity": "high",
                    "confidence": 0.95,
                    "detected_by": "rule-based",
                    "description": "Negative balance with completed transaction status",
                    "field_name": "balance",
                    "original_value": str(row.get('balance'))
                })

            # Rule 2: Suspicious amount (extremely high or low)
            amount = float(row.get('amount', 0))
            if amount > 1000000:
                anomalies.append({
                    "row_index": idx,
                    "transaction_id": row.get('transaction_id'),
                    "anomaly_type": "suspicious_amount",
                    "severity": "medium",
                    "confidence": 0.80,
                    "detected_by": "rule-based",
                    "description": f"Unusually high transaction amount: ${amount:,.2f}",
                    "field_name": "amount",
                    "original_value": str(amount)
                })
            elif amount == 0:
                anomalies.append({
                    "row_index": idx,
                    "transaction_id": row.get('transaction_id'),
                    "anomaly_type": "suspicious_amount",
                    "severity": "low",
                    "confidence": 0.70,
                    "detected_by": "rule-based",
                    "description": "Zero amount transaction",
                    "field_name": "amount",
                    "original_value": "0"
                })

            # Rule 3: Status mismatch
            if (str(row.get('status', '')).lower() == 'failed' and
                float(row.get('amount', 0)) > 0 and
                pd.notna(row.get('balance')) and
                float(row.get('balance', 0)) != float(row.get('amount', 0))):
                # Balance changed despite failed transaction
                anomalies.append({
                    "row_index": idx,
                    "transaction_id": row.get('transaction_id'),
                    "anomaly_type": "status_mismatch",
                    "severity": "high",
                    "confidence": 0.90,
                    "detected_by": "rule-based",
                    "description": "Failed transaction with balance change",
                    "field_name": "status",
                    "original_value": str(row.get('status'))
                })

            # Rule 4: Duplicate transaction ID
            if hasattr(row, 'is_duplicate') and row.is_duplicate:
                anomalies.append({
                    "row_index": idx,
                    "transaction_id": row.get('transaction_id'),
                    "anomaly_type": "duplicate_transaction",
                    "severity": "medium",
                    "confidence": 1.0,
                    "detected_by": "rule-based",
                    "description": "Duplicate transaction ID found",
                    "field_name": "transaction_id",
                    "original_value": str(row.get('transaction_id'))
                })

            # Rule 5: Missing required fields
            required_fields = ['transaction_id', 'customer_id', 'amount', 'status']
            missing_fields = [f for f in required_fields if pd.isna(row.get(f))]
            if missing_fields:
                anomalies.append({
                    "row_index": idx,
                    "transaction_id": row.get('transaction_id'),
                    "anomaly_type": "missing_required_field",
                    "severity": "critical",
                    "confidence": 1.0,
                    "detected_by": "rule-based",
                    "description": f"Missing required fields: {', '.join(missing_fields)}",
                    "field_name": "multiple",
                    "original_value": str(missing_fields)
                })

        return anomalies

    async def _llm_detection(self, idx: int, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform LLM-based anomaly detection for semantic inconsistencies."""
        try:
            result = await watsonx_client.detect_anomaly(transaction_data)

            if result.get('is_anomaly') and result.get('confidence', 0) >= self.confidence_threshold:
                return {
                    "row_index": idx,
                    "transaction_id": transaction_data.get('transaction_id'),
                    "anomaly_type": result.get('anomaly_type', 'semantic_inconsistency'),
                    "severity": result.get('severity', 'medium'),
                    "confidence": result.get('confidence', 0.0),
                    "detected_by": "watsonx-llm",
                    "description": result.get('explanation', 'Semantic inconsistency detected'),
                    "llm_explanation": result.get('explanation'),
                    "context": transaction_data
                }
            return {}

        except Exception as e:
            logger.error(f"LLM detection failed for row {idx}: {e}")
            return {}

    def get_node_config(self) -> Dict[str, Any]:
        """Get node configuration for Watsonx Orchestrate."""
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_type": "anomaly_detection",
            "inputs": {
                "dataframe": {"type": "pandas.DataFrame", "required": True},
                "confidence_threshold": {"type": "float", "default": 0.75}
            },
            "outputs": {
                "dataframe": {"type": "pandas.DataFrame"},
                "metrics": {"type": "dict"},
                "anomalies": {"type": "list"}
            }
        }
