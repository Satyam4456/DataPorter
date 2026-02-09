from abc import ABC, abstractmethod
from typing import Iterator
import pandas as pd
from dataporter.schema.model import TableSchema


class LoaderStrategy(ABC):
    """Base class for data loading strategies."""
    
    strategy_name: str = ""
    
    @abstractmethod
    def load(
        self,
        table_name: str,
        schema: TableSchema,
        chunk_iterator: Iterator[pd.DataFrame],
    ) -> int:
        """
        Load data into table.
        
        Args:
            table_name: Target table name
            schema: TableSchema
            chunk_iterator: Iterator of DataFrame chunks
            
        Returns:
            Total number of rows loaded
        """
        pass