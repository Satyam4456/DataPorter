import re
from typing import Iterator, List, Dict, Tuple, Set, Any
from collections import Counter
import pandas as pd
import numpy as np
from datetime import datetime
from dataporter.schema.infer import SchemaInferenceStrategy
from dataporter.schema.model import TableSchema, ColumnSchema
from dataporter.schema.mapper import ENGINE_TYPE_MAPS
import logging

from pandas.api.types import (
    is_object_dtype,
    is_string_dtype,
    is_bool_dtype,
    is_integer_dtype,
    is_float_dtype,
)

logger = logging.getLogger(__name__)


class PandasSchemaInferencer(SchemaInferenceStrategy):
    """Multi-chunk schema inference using pandas."""
    
    def infer(
        self,
        table_name: str,
        chunk_iterator: Iterator[pd.DataFrame],
        sample_chunks: int = 10,
        confidence_threshold: float = 0.85,
    ) -> TableSchema:
        """Infer schema from multiple chunks."""
        chunks: List[pd.DataFrame] = []
        
        # Collect sample chunks
        for i, chunk in enumerate(chunk_iterator):
            if i >= sample_chunks:
                break
            chunks.append(chunk)
        
        if not chunks:
            raise ValueError("No data chunks available for schema inference")
        
        # Combine for analysis
        combined = pd.concat(chunks, ignore_index=True)
        
        # Infer column schemas
        columns = []
        for col_name in combined.columns:
            col_schema = self._infer_column(
                col_name,
                combined[col_name],
                confidence_threshold,
            )
            columns.append(col_schema)
        
        schema = TableSchema(table_name=table_name, columns=columns)
        logger.info(f"Inferred schema for {table_name}: {len(columns)} columns")
        
        return schema
    
    def _infer_column(
        self,
        col_name: str,
        series: pd.Series,
        confidence_threshold: float,
    ) -> ColumnSchema:
        """Infer schema for a single column."""
        nullable = series.isna().any()
        
        # Get initial pandas dtype
        dtype = series.dtype

        if dtype == 'object':
            inferred_kind, confidence = self._refine_object_column(series)
        elif dtype == 'bool':
            inferred_kind, confidence = 'bool', 1.0
        elif np.issubdtype(dtype, np.integer):
            inferred_kind, confidence = 'int', 1.0
        elif np.issubdtype(dtype, np.floating):
            inferred_kind, confidence = 'float', 1.0
        else:
            inferred_kind, confidence = 'string', 0.5
        
        # Get sample values (non-null)
        samples = series.dropna().unique()[:5].tolist()
        
        # Build db_types for all engines
        db_types = {}
        for engine, type_map in ENGINE_TYPE_MAPS.items():
            db_types[engine] = type_map.get(inferred_kind, 'VARCHAR(255)')
        
        return ColumnSchema(
            name=col_name,
            inferred_kind=inferred_kind,
            nullable=nullable,
            pandas_dtype=str(dtype),
            confidence=confidence,
            db_types=db_types,
            sample_values=samples,
        )
    
    def _refine_object_column(
        self,
        series: pd.Series,
    ) -> Tuple[str, float]:
        """Refine object column type by testing conversions."""
        # Drop nulls for analysis
        clean = series.dropna()
        
        if len(clean) == 0:
            return 'string', 0.5
        
        sample = clean.astype(str).str.strip()
        
        # Test boolean
        bool_score = self._test_boolean(sample)
        if bool_score > 0.9:
            return 'bool', bool_score
        
        # Test integer
        int_score = self._test_integer(sample)
        if int_score > 0.9:
            return 'int', int_score
        
        # Test float
        float_score = self._test_float(sample)
        if float_score > 0.9:
            return 'float', float_score
        
        # Test datetime
        datetime_score = self._test_datetime(sample)
        if datetime_score > 0.85:
            return 'datetime', datetime_score
        
        # Default to string
        return 'string', 0.7
    
    def _test_boolean(self, sample: pd.Series) -> float:
        """Test if sample contains booleans."""
        pattern = r'^(true|false|yes|no|1|0|t|f|y|n)$'
        matches = sample.str.lower().str.match(pattern).sum()
        return matches / len(sample) if len(sample) > 0 else 0
    
    def _test_integer(self, sample: pd.Series) -> float:
        """Test if sample contains integers."""
        try:
            pd.to_numeric(sample, errors='raise')
            # Check if all are whole numbers
            nums = pd.to_numeric(sample)
            return (nums == nums.astype(int)).sum() / len(sample)
        except:
            return 0
    
    def _test_float(self, sample: pd.Series) -> float:
        """Test if sample contains floats."""
        try:
            pd.to_numeric(sample, errors='raise')
            return 1.0
        except:
            return 0
    
    def _test_datetime(self, sample: pd.Series) -> float:
        """Test if sample contains datetimes."""

        # 1. Immediate rejection of quarterly strings (e.g., 2021Q1)
        if sample.str.contains(r'Q[1-4]', regex=True, case=False).any():
            return 0.0
            
        # 2. Require a separator common in actual dates (-, /, or spaces with month names)
        # This prevents single numbers (like "2021") from being seen as dates
        date_pattern = r'[\-/]|\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        if not sample.str.contains(date_pattern, regex=True, case=False).any():
            return 0.0
        
        try:
            pd.to_datetime(sample, errors='raise', format='mixed')
            return 0.9
        except:
            return 0