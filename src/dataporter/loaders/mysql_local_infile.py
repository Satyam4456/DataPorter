from typing import Iterator
import pandas as pd
import tempfile
import os
from pathlib import Path
from dataporter.loaders.base import LoaderStrategy
from dataporter.schema.model import TableSchema
from dataporter.engines.base import Engine
from dataporter.utils.quoting import quote_identifier_mysql
import logging

logger = logging.getLogger(__name__)


class MySQLLocalInfileLoader(LoaderStrategy):
    """MySQL LOAD DATA LOCAL INFILE loader for local deployments."""
    
    strategy_name = "LOAD DATA LOCAL INFILE"
    
    def __init__(self, engine: Engine):
        """
        Initialize loader.
        
        Args:
            engine: MySQLEngine instance
        """
        self.engine = engine
    
    def load(
        self,
        table_name: str,
        schema: TableSchema,
        chunk_iterator: Iterator[pd.DataFrame],
    ) -> int:
        """Load data using MySQL LOAD DATA LOCAL INFILE with raw DBAPI connection."""
        sqlalchemy_engine = self.engine._get_sqlalchemy_engine()
        total_rows = 0
        
        # Track boolean columns for pre-processing
        boolean_columns = {}
        for col in schema.columns:
            if col.inferred_kind == 'bool':
                boolean_columns[col.name] = col.name
        
        logger.debug(f"Boolean columns to convert before loading: {list(boolean_columns.keys())}")
        
        try:
            for i, chunk in enumerate(chunk_iterator):
                # Convert boolean columns BEFORE writing to CSV
                chunk_processed = chunk.copy()
                
                for col_name in boolean_columns.keys():
                    if col_name in chunk_processed.columns:
                        # Convert various boolean representations to 0/1
                        chunk_processed[col_name] = chunk_processed[col_name].apply(
                            self._convert_boolean_value
                        )
                        logger.debug(f"Converted boolean column '{col_name}' in chunk {i}")
                
                # Write processed chunk to temp file
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    delete=False,
                    suffix='.csv',
                    encoding='utf-8',
                    newline='',
                ) as tmp:
                    chunk_processed.to_csv(tmp, index=False, quoting=1, lineterminator='\n')
                    tmp_path = tmp.name
                
                try:
                    # Convert Windows path to forward slashes for MySQL
                    mysql_path = tmp_path.replace('\\', '/')
                    
                    # Build column list
                    columns = ', '.join([f'`{col}`' for col in chunk_processed.columns])
                    
                    # Build LOAD DATA LOCAL INFILE statement
                    load_sql = f"""
                    LOAD DATA LOCAL INFILE '{mysql_path}'
                    INTO TABLE `{table_name}`
                    CHARACTER SET UTF8MB4
                    FIELDS TERMINATED BY ','
                    OPTIONALLY ENCLOSED BY '"'
                    LINES TERMINATED BY '\\n'
                    IGNORE 1 ROWS
                    ({columns})
                    """
                    
                    logger.debug(f"Executing LOAD DATA LOCAL INFILE for chunk {i}")
                    
                    # Use raw DBAPI connection (NOT SQLAlchemy high-level)
                    # This is required for LOAD DATA LOCAL INFILE to work
                    raw_conn = sqlalchemy_engine.raw_connection()
                    try:
                        cursor = raw_conn.cursor()
                        try:
                            cursor.execute(load_sql)
                            raw_conn.commit()
                            
                            rows_in_chunk = len(chunk)
                            total_rows += rows_in_chunk
                            logger.debug(f"Loaded chunk {i}: {rows_in_chunk} rows (total: {total_rows})")
                        finally:
                            cursor.close()
                    finally:
                        raw_conn.close()
                
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            
            logger.info(f"MySQL LOAD DATA LOCAL INFILE completed: {total_rows} rows loaded")
            return total_rows
            
        except Exception as e:
            logger.error(f"MySQL LOAD DATA LOCAL INFILE failed: {e}")
            raise Exception(f"MySQL LOAD DATA LOCAL INFILE failed: {e}") from e
    
    def _convert_boolean_value(self, value):
        """
        Convert various boolean representations to 1 or 0.
        
        Args:
            value: Value to convert
            
        Returns:
            1 for true-like values, 0 for false-like values, original value if unclear
        """
        if pd.isna(value):
            return None
        
        # Convert to string and lowercase for comparison
        str_val = str(value).lower().strip()
        
        # True-like values
        if str_val in ('true', 't', 'yes', 'y', '1', 'on'):
            return 1
        
        # False-like values
        if str_val in ('false', 'f', 'no', 'n', '0', 'off'):
            return 0
        
        # If it's already numeric, return as-is
        try:
            num_val = int(value)
            return 1 if num_val != 0 else 0
        except (ValueError, TypeError):
            pass
        
        # Default: treat non-zero as true
        logger.warning(f"Could not convert boolean value: {value}, defaulting to 0")
        return 0