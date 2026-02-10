from typing import Iterator
import pandas as pd
from dataporter.loaders.base import LoaderStrategy
from dataporter.schema.model import TableSchema
from dataporter.engines.base import Engine
from dataporter.config import MYSQL_DEFAULT_CHUNKSIZE
from sqlalchemy import BIGINT, text, Integer, Float, DateTime, Text, inspect
from sqlalchemy.dialects.mysql import TINYINT
import logging

logger = logging.getLogger(__name__)


class MySQLToSqlLoader(LoaderStrategy):
    """MySQL pandas.to_sql loader with proper schema handling."""
    
    strategy_name = "pandas.to_sql"
    
    def __init__(self, engine: Engine, chunksize: int = MYSQL_DEFAULT_CHUNKSIZE):
        """
        Initialize loader.
        
        Args:
            engine: MySQLEngine instance
            chunksize: Rows per chunk for to_sql
        """
        self.engine = engine
        self.chunksize = chunksize
    
    def load(
        self,
        table_name: str,
        schema: TableSchema,
        chunk_iterator: Iterator[pd.DataFrame],
    ) -> int:
        """Load data using pandas.to_sql with proper type conversion."""
        sqlalchemy_engine = self.engine._get_sqlalchemy_engine()
        total_rows = 0
        table_created = False
        
        try:
            for i, chunk in enumerate(chunk_iterator):
                # Skip empty chunks
                if len(chunk) == 0:
                    logger.debug(f"Skipping empty chunk {i}")
                    continue
                
                # Convert data types before loading
                chunk_converted = self._convert_chunk_types(chunk, schema)
                
                # Create table on first chunk only
                if not table_created:
                    logger.debug(f"Creating table '{table_name}' with schema")
                    
                    # Get SQLAlchemy types
                    dtype_map = self._get_sqlalchemy_column_types(schema)
                    
                    # Write first chunk with dtype to create table
                    chunk_converted.to_sql(
                        table_name,
                        con=sqlalchemy_engine,
                        if_exists='append',
                        index=False,
                        dtype=dtype_map,
                    )
                    table_created = True
                    logger.info(f"Table '{table_name}' created with proper column types")
                else:
                    # Append subsequent chunks
                    chunk_converted.to_sql(
                        table_name,
                        con=sqlalchemy_engine,
                        if_exists='append',
                        index=False,
                    )
                
                rows_in_chunk = len(chunk)
                total_rows += rows_in_chunk
                logger.debug(f"Loaded chunk {i}: {rows_in_chunk} rows (total: {total_rows})")
            
            logger.info(f"MySQL to_sql completed: {total_rows} rows loaded")
            return total_rows
            
        except Exception as e:
            logger.error(f"MySQL to_sql failed: {e}")
            raise Exception(f"MySQL to_sql failed: {e}") from e
    
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
                    )
                    chunk_converted[col.name] = pd.to_numeric(
                        chunk_converted[col.name],
                        errors='coerce'
                    ).astype('Int64')
                    
                elif col_kind == 'datetime':
                    chunk_converted[col.name] = pd.to_datetime(
                        chunk_converted[col.name],
                        errors='coerce'
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to convert column '{col.name}' to {col_kind}: {e}")
        
        return chunk_converted
    
    def _get_sqlalchemy_column_types(self, schema: TableSchema) -> dict:
        """Get SQLAlchemy column type mapping for table creation."""
        type_map = {}
        
        for col in schema.columns:
            col_kind = col.inferred_kind
            
            if col_kind == 'int':
                type_map[col.name] = BIGINT()
                
            elif col_kind == 'float':
                type_map[col.name] = Float()
                
            elif col_kind == 'bool':
                type_map[col.name] = TINYINT()
                
            elif col_kind == 'datetime':
                type_map[col.name] = DateTime()
                
            elif col_kind == 'string':
                type_map[col.name] = Text()
        
        return type_map
    
    def _convert_boolean_value(self, value):
        """Convert various boolean representations to 1 or 0."""
        if pd.isna(value):
            return None
        
        str_val = str(value).lower().strip()
        
        if str_val in ('true', 't', 'yes', 'y', '1', 'on'):
            return 1
        
        if str_val in ('false', 'f', 'no', 'n', '0', 'off'):
            return 0
        
        try:
            num_val = int(value)
            return 1 if num_val != 0 else 0
        except (ValueError, TypeError):
            pass
        
        logger.warning(f"Could not convert boolean value: {value}, defaulting to 0")
        return 0