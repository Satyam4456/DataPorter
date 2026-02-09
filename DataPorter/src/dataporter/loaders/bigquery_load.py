from typing import Iterator
import pandas as pd
from google.cloud import bigquery
from dataporter.loaders.base import LoaderStrategy
from dataporter.schema.model import TableSchema
from dataporter.engines.base import Engine
import logging

logger = logging.getLogger(__name__)


class BigQueryLoadLoader(LoaderStrategy):
    """BigQuery Load Job loader - fast bulk loading."""
    
    strategy_name = "BigQuery Load Job"
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def load(
        self,
        table_name: str,
        schema: TableSchema,
        chunk_iterator: Iterator[pd.DataFrame],
    ) -> int:
        """Load data using BigQuery Load Jobs."""
        client = self.engine._get_client()
        project_id = self.engine.config.get('project_id')
        dataset = self.engine.config.get('dataset')
        table_ref = f"{project_id}.{dataset}.{table_name}"
        
        total_rows = 0
        
        try:
            for i, chunk in enumerate(chunk_iterator):
                if len(chunk) == 0:
                    continue
                
                # Convert data types
                chunk_converted = self._convert_chunk_types(chunk, schema)
                
                logger.info(f"Loading chunk {i}: {len(chunk)} rows to {table_ref}")
                
                # Load job configuration
                job_config = bigquery.LoadJobConfig()
                job_config.autodetect = False
                job_config.schema = self.engine._get_bigquery_schema(schema)
                job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND
                
                # Load data
                load_job = client.load_table_from_dataframe(
                    chunk_converted,
                    table_ref,
                    job_config=job_config,
                )
                
                # Wait for job to complete
                load_job.result()
                
                rows_in_chunk = len(chunk)
                total_rows += rows_in_chunk
                logger.debug(f"Loaded chunk {i}: {rows_in_chunk} rows (total: {total_rows})")
            
            logger.info(f"BigQuery Load completed: {total_rows} rows loaded")
            return total_rows
            
        except Exception as e:
            logger.error(f"BigQuery Load failed: {e}")
            raise Exception(f"BigQuery Load failed: {e}") from e
    
    def _convert_chunk_types(self, chunk: pd.DataFrame, schema: TableSchema) -> pd.DataFrame:
        """Convert chunk data types based on schema."""
        chunk_converted = chunk.copy()
        
        for col in schema.columns:
            if col.name not in chunk_converted.columns:
                continue
            
            col_kind = col.inferred_kind
            
            try:
                if col_kind == 'int':
                    chunk_converted[col.name] = pd.to_numeric(
                        chunk_converted[col.name],
                        errors='coerce'
                    ).astype('Int64')
                    
                elif col_kind == 'float':
                    chunk_converted[col.name] = pd.to_numeric(
                        chunk_converted[col.name],
                        errors='coerce'
                    )
                    
                elif col_kind == 'bool':
                    chunk_converted[col.name] = chunk_converted[col.name].apply(
                        self._convert_boolean_value
                    ).astype('Int64')
                    
                elif col_kind == 'datetime':
                    chunk_converted[col.name] = pd.to_datetime(
                        chunk_converted[col.name],
                        errors='coerce'
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to convert column '{col.name}': {e}")
        
        return chunk_converted
    
    def _convert_boolean_value(self, value):
        """Convert boolean value to 1 or 0."""
        if pd.isna(value):
            return None
        
        str_val = str(value).lower().strip()
        
        if str_val in ('true', 't', 'yes', 'y', '1', 'on'):
            return 1
        if str_val in ('false', 'f', 'no', 'n', '0', 'off'):
            return 0
        
        try:
            return 1 if int(value) != 0 else 0
        except (ValueError, TypeError):
            return 0
