"""Data Ingestion Node - Converts raw sources to standardized dataframe."""
import pandas as pd
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class IngestionNode:

    def __init__(self):
        self.node_id = "ingestion_node"
        self.node_name = "Data Ingestion Node"

    async def execute(
        self,
        source_type: str,
        source_path: Optional[str] = None,
        connection_string: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute the ingestion node.

        Args:
            source_type: Type of data source (csv, sql, api)
            source_path: File path for CSV
            connection_string: Database connection for SQL
            api_endpoint: API URL for API sources

        Returns:
            Dictionary with ingestion results and dataframe
        """
        logger.info(f"Starting ingestion for source_type: {source_type}")

        try:
            if source_type == "csv":
                df = await self._ingest_csv(source_path)
            elif source_type == "sql":
                df = await self._ingest_sql(connection_string, kwargs.get("query"))
            elif source_type == "api":
                df = await self._ingest_api(api_endpoint)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")

            df = self._standardize_columns(df)

            result = {
                "success": True,
                "node_id": self.node_id,
                "source_type": source_type,
                "rows_ingested": len(df),
                "columns": list(df.columns),
                "dataframe": df,
                "metadata": {
                    "shape": df.shape,
                    "dtypes": df.dtypes.astype(str).to_dict(),
                    "memory_usage": df.memory_usage(deep=True).sum()
                }
            }

            logger.info(f"Ingestion complete: {len(df)} rows, {len(df.columns)} columns")
            return result

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return {
                "success": False,
                "node_id": self.node_id,
                "error": str(e),
                "dataframe": pd.DataFrame()
            }

    async def _ingest_csv(self, file_path: str) -> pd.DataFrame:
        logger.info(f"Reading CSV file: {file_path}")

        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

        for encoding in encodings:
            try:
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    parse_dates=['date', 'transaction_date'],
                    infer_datetime_format=True,
                    low_memory=False
                )
                logger.info(f"Successfully read CSV with {encoding} encoding")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                if encoding == encodings[-1]:
                    raise e
                continue

        raise ValueError(f"Could not read CSV file with any supported encoding")

    async def _ingest_sql(self, connection_string: str, query: Optional[str] = None) -> pd.DataFrame:
        logger.info("Reading from SQL database")

        from sqlalchemy import create_engine

        engine = create_engine(connection_string)

        if not query:
            query = "SELECT * FROM transactions"

        df = pd.read_sql(query, engine)
        logger.info(f"Read {len(df)} rows from database")

        return df

    async def _ingest_api(self, api_endpoint: str) -> pd.DataFrame:
        logger.info(f"Fetching data from API: {api_endpoint}")

        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(api_endpoint, timeout=30.0)
            response.raise_for_status()

            data = response.json()

            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                elif 'records' in data:
                    df = pd.DataFrame(data['records'])
                else:
                    df = pd.DataFrame([data])
            else:
                raise ValueError("Unexpected API response format")

            logger.info(f"Fetched {len(df)} records from API")
            return df

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')

        column_mappings = {
            'txn_id': 'transaction_id',
            'trans_id': 'transaction_id',
            'id': 'transaction_id',
            'cust_id': 'customer_id',
            'customer': 'customer_id',
            'amt': 'amount',
            'txn_amount': 'amount',
            'trans_date': 'transaction_date',
            'txn_date': 'transaction_date',
            'date': 'transaction_date',
            'type': 'transaction_type',
            'txn_type': 'transaction_type',
            'desc': 'description',
            'txn_desc': 'description',
        }

        df.rename(columns=column_mappings, inplace=True)

        logger.info(f"Standardized columns: {list(df.columns)}")
        return df

    def get_node_config(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_type": "ingestion",
            "inputs": {
                "source_type": {"type": "string", "required": True},
                "source_path": {"type": "string", "required": False},
                "connection_string": {"type": "string", "required": False},
                "api_endpoint": {"type": "string", "required": False},
            },
            "outputs": {
                "dataframe": {"type": "pandas.DataFrame"},
                "rows_ingested": {"type": "integer"},
                "columns": {"type": "list"},
                "metadata": {"type": "dict"}
            }
        }
