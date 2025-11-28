"""IBM Watsonx AI client for model inference and orchestration."""
from typing import Optional, Dict, Any, List
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class WatsonxClient:
    """Client for interacting with IBM Watsonx.ai."""

    def __init__(self):
        """Initialize Watsonx client with credentials."""
        self.credentials = Credentials(
            url=settings.WATSONX_URL,
            api_key=settings.WATSONX_API_KEY,
        )

        self.client = APIClient(self.credentials)
        self.project_id = settings.WATSONX_PROJECT_ID
        self.model_id = settings.WATSONX_MODEL_ID

        # Initialize model inference
        self.model = None
        if self.credentials.api_key and self.project_id:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize the foundation model for inference."""
        try:
            self.model = ModelInference(
                model_id=self.model_id,
                api_client=self.client,
                project_id=self.project_id,
                params={
                    GenParams.MAX_NEW_TOKENS: settings.WATSONX_MAX_TOKENS,
                    GenParams.TEMPERATURE: settings.WATSONX_TEMPERATURE,
                    GenParams.TOP_K: 50,
                    GenParams.TOP_P: 1.0,
                }
            )
            logger.info(f"Initialized Watsonx model: {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Watsonx model: {e}")
            self.model = None

    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate text using Watsonx foundation model.

        Args:
            prompt: Input prompt for text generation
            max_tokens: Maximum tokens to generate (overrides default)
            temperature: Sampling temperature (overrides default)

        Returns:
            Generated text response
        """
        if not self.model:
            raise ValueError("Watsonx model not initialized. Check API credentials.")

        try:
            params = {}
            if max_tokens:
                params[GenParams.MAX_NEW_TOKENS] = max_tokens
            if temperature is not None:
                params[GenParams.TEMPERATURE] = temperature

            response = self.model.generate(prompt=prompt, params=params if params else None)

            # Extract generated text from response
            if isinstance(response, dict):
                return response.get("results", [{}])[0].get("generated_text", "")
            return str(response)

        except Exception as e:
            logger.error(f"Error generating text with Watsonx: {e}")
            raise

    async def detect_anomaly(
        self,
        transaction_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect anomalies in transaction data using LLM.

        Args:
            transaction_data: Transaction record to analyze
            context: Additional context for anomaly detection

        Returns:
            Dictionary with anomaly detection results
        """
        prompt = self._build_anomaly_detection_prompt(transaction_data, context)

        try:
            response = await self.generate_text(prompt, max_tokens=500, temperature=0.3)
            return self._parse_anomaly_response(response, transaction_data)
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {
                "is_anomaly": False,
                "confidence": 0.0,
                "explanation": f"Error: {str(e)}"
            }

    def _build_anomaly_detection_prompt(
        self,
        transaction: Dict[str, Any],
        context: Optional[str] = None
    ) -> str:
        """Build prompt for anomaly detection."""
        prompt = f"""You are a banking fraud detection expert. Analyze the following transaction for anomalies or suspicious patterns.

Transaction Details:
- Transaction ID: {transaction.get('transaction_id', 'N/A')}
- Customer ID: {transaction.get('customer_id', 'N/A')}
- Amount: {transaction.get('amount', 'N/A')} {transaction.get('currency', 'USD')}
- Balance: {transaction.get('balance', 'N/A')}
- Date: {transaction.get('transaction_date', 'N/A')}
- Type: {transaction.get('transaction_type', 'N/A')}
- Status: {transaction.get('status', 'N/A')}
- Description: {transaction.get('description', 'N/A')}

{f"Additional Context: {context}" if context else ""}

Analyze this transaction for the following types of anomalies:
1. Negative balance with completed status
2. Suspicious amount patterns (very high or very low)
3. Invalid date/time inconsistencies
4. Status mismatches with transaction type
5. Semantic inconsistencies in description vs. amount/type

Respond in the following format:
IS_ANOMALY: [YES/NO]
CONFIDENCE: [0.0-1.0]
ANOMALY_TYPE: [type if anomaly detected]
SEVERITY: [LOW/MEDIUM/HIGH/CRITICAL]
EXPLANATION: [Brief explanation]
"""
        return prompt

    def _parse_anomaly_response(
        self,
        response: str,
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse LLM response for anomaly detection."""
        lines = response.strip().split('\n')
        result = {
            "is_anomaly": False,
            "confidence": 0.0,
            "anomaly_type": "other",
            "severity": "medium",
            "explanation": response,
            "transaction_id": transaction.get("transaction_id"),
            "detected_by": "watsonx-llm"
        }

        for line in lines:
            line = line.strip()
            if line.startswith("IS_ANOMALY:"):
                result["is_anomaly"] = "YES" in line.upper()
            elif line.startswith("CONFIDENCE:"):
                try:
                    result["confidence"] = float(line.split(":")[-1].strip())
                except ValueError:
                    pass
            elif line.startswith("ANOMALY_TYPE:"):
                result["anomaly_type"] = line.split(":")[-1].strip().lower().replace(" ", "_")
            elif line.startswith("SEVERITY:"):
                result["severity"] = line.split(":")[-1].strip().lower()
            elif line.startswith("EXPLANATION:"):
                result["explanation"] = line.split(":", 1)[-1].strip()

        return result

    async def validate_data_quality(
        self,
        data_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to assess overall data quality.

        Args:
            data_summary: Summary statistics of the dataset

        Returns:
            Quality assessment results
        """
        prompt = f"""Analyze the following dataset quality metrics and provide an assessment:

Dataset Summary:
- Total Rows: {data_summary.get('total_rows', 0)}
- Null Percentage: {data_summary.get('null_percentage', 0)}%
- Duplicate Count: {data_summary.get('duplicates', 0)}
- Invalid Formats: {data_summary.get('invalid_formats', 0)}
- Date Range Issues: {data_summary.get('date_issues', 0)}

Provide a quality score (0-100) and recommendations for improvement.

Format:
QUALITY_SCORE: [0-100]
RECOMMENDATIONS: [List of recommendations]
"""

        try:
            response = await self.generate_text(prompt, max_tokens=500)
            return self._parse_quality_response(response)
        except Exception as e:
            logger.error(f"Error in quality validation: {e}")
            return {"quality_score": 0, "recommendations": []}

    def _parse_quality_response(self, response: str) -> Dict[str, Any]:
        """Parse quality assessment response."""
        result = {
            "quality_score": 0.0,
            "recommendations": []
        }

        lines = response.strip().split('\n')
        for line in lines:
            if line.startswith("QUALITY_SCORE:"):
                try:
                    result["quality_score"] = float(line.split(":")[-1].strip())
                except ValueError:
                    pass
            elif line.startswith("RECOMMENDATIONS:"):
                recs = line.split(":", 1)[-1].strip()
                result["recommendations"] = [r.strip() for r in recs.split(",")]

        return result


# Global client instance
watsonx_client = WatsonxClient()
