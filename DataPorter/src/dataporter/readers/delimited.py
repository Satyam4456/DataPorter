import pandas as pd
from typing import Iterator, Optional
from dataporter.readers.base import Reader
from dataporter.exceptions import ReaderError
import logging

logger = logging.getLogger(__name__)


class DelimitedReader(Reader):
    """Reader for CSV/TSV and other delimited text files."""
    
    def __init__(
        self,
        delimiter: str = ',',
        encoding: str = 'utf-8',
        skip_rows: int = 0,
        **kwargs,
    ):
        """
        Initialize delimited reader.
        
        Args:
            delimiter: Field delimiter (default ',')
            encoding: File encoding (default 'utf-8')
            skip_rows: Number of rows to skip at start
            **kwargs: Additional pandas read_csv arguments
        """
        self.delimiter = delimiter
        self.encoding = encoding
        self.skip_rows = skip_rows
        self.kwargs = kwargs
    
    def read_chunks(
        self,
        file_path: str,
        chunksize: int = 100000,
    ) -> Iterator[pd.DataFrame]:
        """
        Read delimited file in chunks.
        
        Args:
            file_path: Path to file
            chunksize: Rows per chunk
            
        Yields:
            pandas DataFrames
            
        Raises:
            ReaderError: If file cannot be read
        """
        try:
            logger.info(
                f"Reading delimited file: {file_path}, "
                f"delimiter='{self.delimiter}', chunksize={chunksize}"
            )
            
            reader = pd.read_csv(
                file_path,
                sep=self.delimiter,
                encoding=self.encoding,
                skiprows=self.skip_rows,
                chunksize=chunksize,
                dtype=str,  # Read all as strings initially
                **self.kwargs,
            )
            
            for i, chunk in enumerate(reader):
                logger.debug(f"Read chunk {i}: {len(chunk)} rows")
                yield chunk
                
        except FileNotFoundError as e:
            raise ReaderError(f"File not found: {file_path}") from e
        except Exception as e:
            raise ReaderError(f"Error reading file {file_path}: {e}") from e