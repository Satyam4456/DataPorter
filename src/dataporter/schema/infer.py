from abc import ABC, abstractmethod
from typing import Iterator
import pandas as pd
from dataporter.schema.model import TableSchema, ColumnSchema


class SchemaInferenceStrategy(ABC):
    """Base class for schema inference strategies."""
    
    @abstractmethod
    def infer(
        self,
        table_name: str,
        chunk_iterator: Iterator[pd.DataFrame],
        sample_chunks: int = 10,
        confidence_threshold: float = 0.85,
    ) -> TableSchema:
        """
        Infer schema from file chunks.
        
        Args:
            table_name: Name of target table
            chunk_iterator: Iterator yielding pandas DataFrames
            sample_chunks: Number of chunks to sample
            confidence_threshold: Minimum confidence for type inference
            
        Returns:
            TableSchema with inferred column schemas
        """
        pass