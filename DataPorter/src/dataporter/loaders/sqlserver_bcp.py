from typing import Iterator
import pandas as pd
import tempfile
import os
import csv
from dataporter.loaders.base import LoaderStrategy
from dataporter.schema.model import TableSchema
from dataporter.engines.base import Engine
from dataporter.utils.subprocess import run_subprocess
import logging

logger = logging.getLogger(__name__)


class SQLServerBcpLoader(LoaderStrategy):
    """SQL Server BCP (Bulk Copy Program) loader - fastest method."""
    
    strategy_name = "SQL Server BCP"
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def load(
        self,
        table_name: str,
        schema: TableSchema,
        chunk_iterator: Iterator[pd.DataFrame],
    ) -> int:
        """Load data using SQL Server BCP command."""
        total_rows = 0
        
        try:
            for i, chunk in enumerate(chunk_iterator):
                if len(chunk) == 0:
                    continue
                
                # Clean data: convert empty strings and 'NA' to NaN for numeric columns
                chunk = self._clean_numeric_columns(chunk, schema)
                
                # Convert boolean columns to 1/0 for SQL Server BIT type
                chunk = self._convert_boolean_for_bcp(chunk, schema)
                
                # Write chunk to temp CSV file WITHOUT quotes
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    delete=False,
                    suffix='.csv',
                    newline='',
                    encoding='utf-8'
                ) as tmp:
                    chunk.to_csv(
                        tmp,
                        index=False,
                        sep="\t",
                        quoting=csv.QUOTE_NONE,  # Don't quote anything
                        escapechar='\\',  # Escape special characters
                        na_rep='',  # Empty string for NaN (not 'NaN')
                        encoding='utf-8'
                    )
                    tmp_path = tmp.name
                
                # Error log file
                error_log = os.path.join(
                    os.path.dirname(tmp_path),
                    f"bcp_error_{i}.log"
                )
                
                try:
                    # Build BCP command
                    host = self.engine.config.get('host', 'localhost')
                    port = self.engine.config.get('port', 1433)
                    user = self.engine.config.get('user', 'sa')
                    password = self.engine.config.get('password', '')
                    database = self.engine.config.get('database', 'master')
                    
                    # Format username for Azure SQL if needed
                    if '.database.windows.net' in host and '@' not in user:
                        user = f"{user}@{host.split('.')[0]}"
                    
                    # Table name WITHOUT brackets: dbo.table_name
                    bcp_table = f"dbo.{table_name}"
                    
                    # BCP command with -d flag for database specification
                    bcp_cmd = [
                        'bcp',
                        bcp_table,
                        'in',
                        tmp_path,
                        '-S', f"{host},{port}",
                        '-d', database,  # Explicitly specify database
                        '-U', user,
                        '-P', password,
                        '-F', '2',  # Skip header row
                        '-c',  # Character format
                        '-t', '\t',  # Comma delimiter
                        '-q',  # Quoted identifiers
                        '-e', error_log,  # Error file for diagnostics
                    ]
                    
                    logger.info(f"Executing BCP for chunk {i}: {len(chunk)} rows")
                    logger.debug(f"BCP Table: {bcp_table}, Database: {database}")
                    
                    # Run BCP
                    run_subprocess(bcp_cmd, timeout=3600)
                    
                    rows_in_chunk = len(chunk)
                    total_rows += rows_in_chunk
                    logger.info(f"Loaded chunk {i}: {rows_in_chunk} rows (total: {total_rows})")
                    
                except Exception as e:
                    # Read and print error file
                    if os.path.exists(error_log):
                        logger.error(f"BCP Error Log ({error_log}):")
                        try:
                            with open(error_log, 'r', encoding='utf-8') as f:
                                lines = f.readlines()[:5]  # First 5 lines
                                for line in lines:
                                    logger.error(f"  {line.strip()}")
                        except Exception as read_err:
                            logger.error(f"Could not read error log: {read_err}")
                    
                    raise e
                    
                finally:
                    # Clean up temp files
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    if os.path.exists(error_log):
                        os.unlink(error_log)
            
            logger.info(f"SQL Server BCP completed: {total_rows} rows loaded")
            return total_rows
            
        except Exception as e:
            logger.error(f"SQL Server BCP failed: {e}")
            raise Exception(f"SQL Server BCP failed: {e}") from e
    
    def _clean_numeric_columns(self, chunk: pd.DataFrame, schema: TableSchema) -> pd.DataFrame:
        """
        Clean numeric columns: convert empty strings and 'NA' to NaN.
        Empty strings will be exported as empty (not 'NaN'), which SQL Server treats as NULL.
        """
        chunk_clean = chunk.copy()
        
        for col in schema.columns:
            if col.name not in chunk_clean.columns:
                continue
            
            # If column is numeric, clean it
            if col.inferred_kind in ('int', 'float'):
                # Replace empty strings, 'NA', 'na', 'N/A' with NaN
                chunk_clean[col.name] = chunk_clean[col.name].replace(
                    ['', 'NA', 'na', 'N/A', 'null', 'NULL', 'None'],
                    pd.NA
                )
                logger.debug(f"Cleaned numeric column: {col.name}")
        
        return chunk_clean
    
    def _convert_boolean_for_bcp(self, chunk: pd.DataFrame, schema: TableSchema) -> pd.DataFrame:
        """
        Convert boolean columns to 1/0 integers for SQL Server BIT type.
        SQL Server BCP requires BIT columns to be represented as 1 and 0, not 'true'/'false'.
        """
        chunk_converted = chunk.copy()
        
        for col in schema.columns:
            if col.name not in chunk_converted.columns:
                continue
            
            # If column is boolean, convert to 1/0
            if col.inferred_kind == 'bool':
                chunk_converted[col.name] = chunk_converted[col.name].apply(
                    self._convert_boolean_value
                )
                logger.debug(f"Converted boolean column to 1/0: {col.name}")
        
        return chunk_converted
    
    def _convert_boolean_value(self, value):
        """
        Convert various boolean representations to 1 or 0.
        Handles: true, false, 'true', 'false', 1, 0, None, NaN
        """
        if pd.isna(value):
            return pd.NA  # Keep NaN as NaN (will export as empty)
        
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