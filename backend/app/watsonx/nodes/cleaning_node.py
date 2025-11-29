"""Cleaning Node - Performs imputations, normalization, regex transformations."""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class CleaningNode:

    def __init__(self):
        self.node_id = "cleaning_node"
        self.node_name = "Data Cleaning Node"

    async def execute(self, dataframe: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        logger.info(f"Starting cleaning for {len(dataframe)} rows")

        df = dataframe.copy()
        cleaning_log = []
        rows_modified = 0

        df['original_values'] = df.apply(lambda row: {}, axis=1)
        df['cleaning_actions'] = df.apply(lambda row: [], axis=1)
        df['was_cleaned'] = False

        for idx, row in df.iterrows():
            row_modified = False
            original_values = {}
            actions = []

            if pd.notna(row.get('transaction_id')):
                cleaned_txn_id = self._clean_transaction_id(row['transaction_id'])
                if cleaned_txn_id != row['transaction_id']:
                    original_values['transaction_id'] = row['transaction_id']
                    df.at[idx, 'transaction_id'] = cleaned_txn_id
                    actions.append("Cleaned transaction_id format")
                    row_modified = True

            if pd.notna(row.get('amount')):
                cleaned_amount = self._clean_amount(row['amount'])
                if cleaned_amount != row['amount']:
                    original_values['amount'] = row['amount']
                    df.at[idx, 'amount'] = cleaned_amount
                    actions.append("Normalized amount value")
                    row_modified = True

            if pd.notna(row.get('status')):
                cleaned_status = self._clean_status(row['status'])
                if cleaned_status != row['status']:
                    original_values['status'] = row['status']
                    df.at[idx, 'status'] = cleaned_status
                    actions.append("Standardized status value")
                    row_modified = True

            if pd.notna(row.get('transaction_type')):
                cleaned_type = self._clean_transaction_type(row['transaction_type'])
                if cleaned_type != row['transaction_type']:
                    original_values['transaction_type'] = row['transaction_type']
                    df.at[idx, 'transaction_type'] = cleaned_type
                    actions.append("Standardized transaction_type")
                    row_modified = True

            if pd.notna(row.get('description')):
                cleaned_desc = self._clean_description(row['description'])
                if cleaned_desc != row['description']:
                    original_values['description'] = row['description']
                    df.at[idx, 'description'] = cleaned_desc
                    actions.append("Cleaned description text")
                    row_modified = True

            if pd.isna(row.get('currency')):
                df.at[idx, 'currency'] = 'USD'
                actions.append("Imputed missing currency with USD")
                row_modified = True

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
            "cleaning_log": cleaning_log[:100]
        }

        logger.info(f"Cleaning complete: {rows_modified} rows modified")
        return result

    def _clean_transaction_id(self, value: Any) -> str:
        if pd.isna(value):
            return ""

        txn_id = str(value).strip()

        txn_id = re.sub(r'[^a-zA-Z0-9_-]', '', txn_id)

        return txn_id.upper()

    def _clean_customer_id(self, value: Any) -> str:
        if pd.isna(value):
            return ""

        cust_id = str(value).strip()
        cust_id = re.sub(r'[^a-zA-Z0-9_-]', '', cust_id)
        return cust_id.upper()

    def _clean_amount(self, value: Any) -> float:
        if pd.isna(value):
            return 0.0

        if isinstance(value, str):
            value = re.sub(r'[$€£¥,]', '', value.strip())

            if value.startswith('(') and value.endswith(')'):
                value = '-' + value[1:-1]

        try:
            amount = float(value)
            return round(amount, 2)
        except (ValueError, TypeError):
            return 0.0

    def _clean_status(self, value: Any) -> str:
        if pd.isna(value):
            return "unknown"

        status = str(value).lower().strip()

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
        if pd.isna(value):
            return "unknown"

        trans_type = str(value).lower().strip()

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
        if pd.isna(value):
            return ""

        desc = str(value).strip()

        desc = re.sub(r'\s+', ' ', desc)

        desc = re.sub(r'[^\w\s\-.,!?()]', '', desc)

        return desc

    def _handle_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        duplicates = df[df.duplicated(subset=['transaction_id'], keep='first')]

        if len(duplicates) > 0:
            logger.warning(f"Found {len(duplicates)} duplicate transaction IDs")
            df['is_duplicate'] = df.duplicated(subset=['transaction_id'], keep='first')

        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'description' in df.columns:
            df['description'].fillna('No description', inplace=True)

        if 'transaction_type' in df.columns:
            df['transaction_type'].fillna('unknown', inplace=True)

        if 'balance' in df.columns:
            df['balance'].fillna(method='ffill', inplace=True)

        return df

    def _normalize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'transaction_date' in df.columns:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')

        return df

    def get_node_config(self) -> Dict[str, Any]:
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
