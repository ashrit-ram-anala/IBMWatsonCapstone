"""Cleaning Node - Performs imputations, normalization, regex transformations."""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class CleaningNode:
    """
    Node 3: Cleaning Node
    Performs data cleaning, imputation, and normalization.
    """

    def __init__(self):
        self.node_id = "cleaning_node"
        self.node_name = "Data Cleaning Node"

    async def execute(self, dataframe: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Execute the cleaning node.

        Args:
            dataframe: Input dataframe to clean

        Returns:
            Dictionary with cleaning results
        """
        logger.info(f"Starting cleaning for {len(dataframe)} rows")

        df = dataframe.copy()
        cleaning_log = []
        rows_modified = 0

        # Track original values
        df['original_values'] = df.apply(lambda row: {}, axis=1)
        df['cleaning_actions'] = df.apply(lambda row: [], axis=1)
        df['was_cleaned'] = False

        # Clean each row
        for idx, row in df.iterrows():
            row_modified = False
            original_values = {}
            actions = []

            # Clean transaction_id
            if pd.notna(row.get('transaction_id')):
                cleaned_txn_id = self._clean_transaction_id(row['transaction_id'])
                if cleaned_txn_id != row['transaction_id']:
                    original_values['transaction_id'] = row['transaction_id']
                    df.at[idx, 'transaction_id'] = cleaned_txn_id
                    actions.append("Cleaned transaction_id format")
                    row_modified = True

            # Clean and normalize amount
            if pd.notna(row.get('amount')):
                cleaned_amount = self._clean_amount(row['amount'])
                if cleaned_amount != row['amount']:
                    original_values['amount'] = row['amount']
                    df.at[idx, 'amount'] = cleaned_amount
                    actions.append("Normalized amount value")
                    row_modified = True

            # Clean status
            if pd.notna(row.get('status')):
                cleaned_status = self._clean_status(row['status'])
                if cleaned_status != row['status']:
                    original_values['status'] = row['status']
                    df.at[idx, 'status'] = cleaned_status
                    actions.append("Standardized status value")
                    row_modified = True

            # Clean transaction_type
            if pd.notna(row.get('transaction_type')):
                cleaned_type = self._clean_transaction_type(row['transaction_type'])
                if cleaned_type != row['transaction_type']:
                    original_values['transaction_type'] = row['transaction_type']
                    df.at[idx, 'transaction_type'] = cleaned_type
                    actions.append("Standardized transaction_type")
                    row_modified = True

            # Clean description
            if pd.notna(row.get('description')):
                cleaned_desc = self._clean_description(row['description'])
                if cleaned_desc != row['description']:
                    original_values['description'] = row['description']
                    df.at[idx, 'description'] = cleaned_desc
                    actions.append("Cleaned description text")
                    row_modified = True

            # Handle missing currency
            if pd.isna(row.get('currency')):
                df.at[idx, 'currency'] = 'USD'
                actions.append("Imputed missing currency with USD")
                row_modified = True

            # Clean customer_id
            if pd.notna(row.get('customer_id')):
                cleaned_cust_id = self._clean_customer_id(row['customer_id'])
                if cleaned_cust_id != row['customer_id']:
                    original_values['customer_id'] = row['customer_id']
                    df.at[idx, 'customer_id'] = cleaned_cust_id
                    actions.append("Cleaned customer_id format")
                    row_modified = True

            if row_modified:
                df.at[idx, 'original_values'] = original_values
                df.at[idx, 'cleaning_actions'] = actions
                df.at[idx, 'was_cleaned'] = True
                rows_modified += 1
                cleaning_log.append({
                    "row_index": idx,
                    "actions": actions,
                    "original_values": original_values
                })

        # Perform dataset-level cleaning
        df = self._handle_duplicates(df)
        df = self._handle_missing_values(df)
        df = self._normalize_dates(df)

        result = {
            "success": True,
            "node_id": self.node_id,
            "dataframe": df,
            "metrics": {
                "total_rows": len(df),
                "rows_modified": rows_modified,
                "modification_rate": round(rows_modified / len(df) * 100, 2) if len(df) > 0 else 0,
                "cleaning_actions_count": sum(len(log['actions']) for log in cleaning_log)
            },
            "cleaning_log": cleaning_log[:100]  # Limit to first 100 entries
        }

        logger.info(f"Cleaning complete: {rows_modified} rows modified")
        return result

    def _clean_transaction_id(self, value: Any) -> str:
        """Clean and standardize transaction ID."""
        if pd.isna(value):
            return ""

        # Convert to string and remove extra whitespace
        txn_id = str(value).strip()

        # Remove special characters except hyphens and underscores
        txn_id = re.sub(r'[^a-zA-Z0-9_-]', '', txn_id)

        return txn_id.upper()

    def _clean_customer_id(self, value: Any) -> str:
        """Clean and standardize customer ID."""
        if pd.isna(value):
            return ""

        cust_id = str(value).strip()
        cust_id = re.sub(r'[^a-zA-Z0-9_-]', '', cust_id)
        return cust_id.upper()

    def _clean_amount(self, value: Any) -> float:
        """Clean and normalize amount values."""
        if pd.isna(value):
            return 0.0

        # Handle string amounts with currency symbols
        if isinstance(value, str):
            # Remove currency symbols and commas
            value = re.sub(r'[$€£¥,]', '', value.strip())

            # Handle parentheses (accounting notation for negative)
            if value.startswith('(') and value.endswith(')'):
                value = '-' + value[1:-1]

        try:
            amount = float(value)
            # Round to 2 decimal places
            return round(amount, 2)
        except (ValueError, TypeError):
            return 0.0

    def _clean_status(self, value: Any) -> str:
        """Clean and standardize status values."""
        if pd.isna(value):
            return "unknown"

        status = str(value).lower().strip()

        # Mapping variations to standard statuses
        status_map = {
            'complete': 'completed',
            'success': 'completed',
            'successful': 'completed',
            'approved': 'completed',
            'done': 'completed',
            'fail': 'failed',
            'failure': 'failed',
            'declined': 'failed',
            'rejected': 'failed',
            'cancel': 'cancelled',
            'canceled': 'cancelled',
            'process': 'processing',
            'processing': 'processing',
            'pend': 'pending',
            'waiting': 'pending'
        }

        return status_map.get(status, status)

    def _clean_transaction_type(self, value: Any) -> str:
        """Clean and standardize transaction type."""
        if pd.isna(value):
            return "unknown"

        trans_type = str(value).lower().strip()

        # Mapping variations
        type_map = {
            'dep': 'deposit',
            'credit': 'deposit',
            'withdraw': 'withdrawal',
            'withdrawal': 'withdrawal',
            'debit': 'withdrawal',
            'transfer': 'transfer',
            'xfer': 'transfer',
            'payment': 'payment',
            'pay': 'payment',
            'purchase': 'payment',
            'refund': 'refund',
            'return': 'refund'
        }

        return type_map.get(trans_type, trans_type)

    def _clean_description(self, value: Any) -> str:
        """Clean transaction description text."""
        if pd.isna(value):
            return ""

        desc = str(value).strip()

        # Remove extra whitespace
        desc = re.sub(r'\s+', ' ', desc)

        # Remove special characters that might cause issues
        desc = re.sub(r'[^\w\s\-.,!?()]', '', desc)

        return desc

    def _handle_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove or flag duplicate transactions."""
        # Check for duplicate transaction IDs
        duplicates = df[df.duplicated(subset=['transaction_id'], keep='first')]

        if len(duplicates) > 0:
            logger.warning(f"Found {len(duplicates)} duplicate transaction IDs")
            # Mark duplicates instead of removing them
            df['is_duplicate'] = df.duplicated(subset=['transaction_id'], keep='first')

        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values with appropriate imputation."""
        # Impute missing descriptions with "No description"
        if 'description' in df.columns:
            df['description'].fillna('No description', inplace=True)

        # Impute missing transaction types
        if 'transaction_type' in df.columns:
            df['transaction_type'].fillna('unknown', inplace=True)

        # Impute missing balances with forward fill
        if 'balance' in df.columns:
            df['balance'].fillna(method='ffill', inplace=True)

        return df

    def _normalize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize date formats."""
        if 'transaction_date' in df.columns:
            # Ensure dates are in datetime format
            df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')

        return df

    def get_node_config(self) -> Dict[str, Any]:
        """Get node configuration for Watsonx Orchestrate."""
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_type": "cleaning",
            "inputs": {
                "dataframe": {"type": "pandas.DataFrame", "required": True}
            },
            "outputs": {
                "dataframe": {"type": "pandas.DataFrame"},
                "metrics": {"type": "dict"},
                "cleaning_log": {"type": "list"}
            }
        }
