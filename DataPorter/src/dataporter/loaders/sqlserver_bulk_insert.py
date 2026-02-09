from typing import Iterator
import pandas as pd
import tempfile
import os
from sqlalchemy import text
from dataporter.loaders.base import LoaderStrategy
from dataporter.schema.model import TableSchema
from dataporter.engines.base import Engine
import logging

logger = logging.getLogger(__name__)


class SQLServerBulkInsertLoader(LoaderStrategy):
    """SQL Server BULK INSERT loader for local file access."""
    
    strategy_name = "BULK INSERT"
    
    def __init__(self, engine: Engine):
        """
        Initialize loader.
        
        Args:
            engine: SQLServerEngine instance
        """
        self.engine = engine
    
    def load(
        self,
        table_name: str,
        schema: TableSchema,
        chunk_iterator: Iterator[pd.DataFrame],
    ) -> int:
        """Load data using BULK INSERT."""
        sqlalchemy_engine = self.engine._get_sqlalchemy_engine()
        db_schema = self.engine.config.get('schema', 'dbo')
        total_rows = 0
        
        try:
            for i, chunk in enumerate(chunk_iterator):
                # Write chunk to temp file
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    delete=False,
                    suffix='.csv',
                    newline='',
                ) as tmp:
                    chunk.to_csv(tmp, index=False, sep=',')
                    tmp_path = tmp.name
                
                try:
                    # Build BULK INSERT statement
                    bulk_sql = f"""
                    BULK INSERT [{db_schema}].[{table_name}]
                    FROM '{tmp_path}'
                    WITH (
                        FORMAT = 'CSV',
                        FIRSTROW = 2,
                        FIELDTERMINATOR = ',',
                        ROWTERMINATOR = '\\n',
                        TABLOCK
                    )
                    """
                    
                    with sqlalchemy_engine.connect() as conn:
                        conn.execute(text(bulk_sql))
                        conn.commit()
                    
                    rows_in_chunk = len(chunk)
                    total_rows += rows_in_chunk
                    logger.debug(f"Loaded chunk {i}: {rows_in_chunk} rows (total: {total_rows})")
                
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            
            logger.info(f"SQL Server BULK INSERT completed: {total_rows} rows")
            return total_rows
            
        except Exception as e:
            raise Exception(f"SQL Server BULK INSERT failed: {e}") from e