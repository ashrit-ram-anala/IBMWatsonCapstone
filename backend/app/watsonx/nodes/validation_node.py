"""Schema Validator Node - Enforces banking schema rules."""
import pandas as pd
import logging
from typing import Dict, Any, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class ValidationNode:

    def __init__(self, required_columns: List[str] = None):
        self.node_id = "validation_node"
        self.node_name = "Schema Validator Node"
        self.required_columns = required_columns or [
            "transaction_id",
            "customer_id",
            "amount",
            "transaction_date",
            "status"
        ]

    async def execute(self, dataframe: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        logger.info(f"Starting validation for {len(dataframe)} rows")

        df = dataframe.copy()
        validation_errors = []
        rows_with_errors = []

        missing_columns = self._check_required_columns(df)
        if missing_columns:
            return {
                "success": False,
                "node_id": self.node_id,
                "error": f"Missing required columns: {missing_columns}",
                "dataframe": df
            }

        for idx, row in df.iterrows():
            row_errors = []

            if not self._validate_transaction_id(row.get('transaction_id')):
                row_errors.append({
                    "field": "transaction_id",
                    "error": "Invalid or missing transaction ID",
                    "value": row.get('transaction_id')
                })

            if not self._validate_customer_id(row.get('customer_id')):
                row_errors.append({
                    "field": "customer_id",
                    "error": "Invalid or missing customer ID",
                    "value": row.get('customer_id')
                })

            amount_error = self._validate_amount(row.get('amount'))
            if amount_error:
                row_errors.append({
                    "field": "amount",
                    "error": amount_error,
                    "value": row.get('amount')
                })

            date_error = self._validate_date(row.get('transaction_date'))
            if date_error:
                row_errors.append({
                    "field": "transaction_date",
                    "error": date_error,
                    "value": row.get('transaction_date')
                })

            if not self._validate_status(row.get('status')):
                row_errors.append({
                    "field": "status",
                    "error": "Invalid or missing status",
                    "value": row.get('status')
                })

            if row_errors:
                validation_errors.extend(row_errors)
                rows_with_errors.append(idx)
                df.at[idx, 'is_valid'] = False
                df.at[idx, 'validation_errors'] = str(row_errors)
            else:
                df.at[idx, 'is_valid'] = True

        total_rows = len(df)
        valid_rows = total_rows - len(rows_with_errors)
        validation_rate = (valid_rows / total_rows * 100) if total_rows > 0 else 0

        result = {
            "success": True,
            "node_id": self.node_id,
            "dataframe": df,
            "metrics": {
                "total_rows": total_rows,
                "valid_rows": valid_rows,
                "invalid_rows": len(rows_with_errors),
                "validation_rate": round(validation_rate, 2),
                "error_count": len(validation_errors)
            },
            "validation_errors": validation_errors[:100],
            "rows_with_errors": rows_with_errors[:100]
        }

        logger.info(f"Validation complete: {valid_rows}/{total_rows} valid rows ({validation_rate:.2f}%)")
        return result

    def _check_required_columns(self, df: pd.DataFrame) -> List[str]:
        missing = [col for col in self.required_columns if col not in df.columns]
        return missing

    def _validate_transaction_id(self, value: Any) -> bool:
        if pd.isna(value):
            return False
        if not isinstance(value, str):
            value = str(value)
        return len(value) > 0

    def _validate_customer_id(self, value: Any) -> bool:
        if pd.isna(value):
            return False
        if not isinstance(value, str):
            value = str(value)
        return len(value) > 0

    def _validate_amount(self, value: Any) -> str:
        if pd.isna(value):
            return "Amount is missing"

        try:
            amount = float(value)
            if amount == 0:
                return "Amount is zero"
            return ""
        except (ValueError, TypeError):
            return "Amount is not a valid number"

    def _validate_date(self, value: Any) -> str:
        if pd.isna(value):
            return "Date is missing"

        if isinstance(value, (datetime, pd.Timestamp)):
            now = datetime.now()
            if value > now:
                return "Date is in the future"
            if (now - value).days > 3650:
                return "Date is more than 10 years old"
            return ""

        try:
            date = pd.to_datetime(value)
            now = datetime.now()
            if date > now:
                return "Date is in the future"
            if (now - date).days > 3650:
                return "Date is more than 10 years old"
            return ""
        except (ValueError, TypeError):
            return "Invalid date format"

    def _validate_status(self, value: Any) -> bool:
        if pd.isna(value):
            return False

        valid_statuses = [
            'completed', 'pending', 'failed', 'cancelled',
            'success', 'approved', 'declined', 'processing'
        ]

        if isinstance(value, str):
            return value.lower() in valid_statuses

        return False

    def get_node_config(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_type": "validation",
            "inputs": {
                "dataframe": {"type": "pandas.DataFrame", "required": True}
            },
            "outputs": {
                "dataframe": {"type": "pandas.DataFrame"},
                "metrics": {"type": "dict"},
                "validation_errors": {"type": "list"}
            }
        }
