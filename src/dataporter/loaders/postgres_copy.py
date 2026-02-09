from typing import Iterator
import pandas as pd
import io
from dataporter.loaders.base import LoaderStrategy
from dataporter.schema.model import TableSchema
from dataporter.engines.base import Engine
import logging

logger = logging.getLogger(__name__)


class PostgresCopyLoader(LoaderStrategy):
    """PostgreSQL COPY loader using psycopg2."""
    
    strategy_name = "PostgreSQL COPY"
    
    def __init__(self, engine: Engine):
        """
        Initialize loader.
        
        Args:
            engine: PostgresEngine instance
        """
        self.engine = engine
    
    def load(
        self,
        table_name: str,
        schema: TableSchema,
        chunk_iterator: Iterator[pd.DataFrame],
    ) -> int:
        """Load data using PostgreSQL COPY command."""
        conn = self.engine._get_connection()
        total_rows = 0
        
        try:
            for i, chunk in enumerate(chunk_iterator):
                if len(chunk) == 0:
                    continue
                
                # Convert chunk to CSV buffer for COPY
                # IMPORTANT: Don't include header in buffer (COPY will skip line 1)
                buffer = io.StringIO()
                chunk.to_csv(buffer, index=False, header=False)  # header=False - no header row!
                buffer.seek(0)
                
                # Build COPY command for psycopg2
                columns = ', '.join([f'"{col}"' for col in chunk.columns])
                copy_sql = (
                    f'COPY "{table_name}" ({columns}) '
                    f'FROM STDIN WITH (FORMAT CSV, DELIMITER \',\', QUOTE \'"\', ESCAPE \'\\\')'
                )
                
                logger.debug(f"Executing COPY for chunk {i}")
                
                # Execute COPY using psycopg2's copy_expert
                cur = conn.cursor()
                try:
                    cur.copy_expert(copy_sql, buffer)
                    conn.commit()
                    
                    rows_in_chunk = len(chunk)
                    total_rows += rows_in_chunk
                    logger.debug(f"Loaded chunk {i}: {rows_in_chunk} rows")
                finally:
                    cur.close()
            
            logger.info(f"PostgreSQL COPY completed: {total_rows} rows loaded")
            return total_rows
            
        except Exception as e:
            logger.error(f"PostgreSQL COPY failed: {e}")
            raise Exception(f"PostgreSQL COPY failed: {e}") from e