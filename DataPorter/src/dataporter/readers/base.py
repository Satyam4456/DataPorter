from abc import ABC, abstractmethod
from typing import Iterator
import pandas as pd


class Reader(ABC):
    """Base class for file readers."""
    
    @abstractmethod
    def read_chunks(self, file_path: str, chunksize: int) -> Iterator[pd.DataFrame]:
        """
        Read file and yield chunks as DataFrames.
        
        Args:
            file_path: Path to file
            chunksize: Rows per chunk
            
        Yields:
            pandas DataFrames of chunksize rows
        """
        pass