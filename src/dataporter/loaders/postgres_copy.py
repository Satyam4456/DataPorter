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
        conn = self.engine._get_connection()
        total_rows = 0

        try:
            for i, chunk in enumerate(chunk_iterator):
                if len(chunk) == 0:
                    continue

                # psycopg3 COPY requires BYTES, not str
                buffer = io.BytesIO()
                chunk.to_csv(
                    buffer,
                    index=False,
                    header=False,
                    encoding="utf-8"
                )
                buffer.seek(0)

                columns = ", ".join(f'"{col}"' for col in chunk.columns)

                copy_sql = (
                    f'COPY "{table_name}" ({columns}) '
                    f"FROM STDIN WITH (FORMAT CSV, DELIMITER ',', QUOTE '\"')"
                )

                logger.debug(f"Executing COPY for chunk {i}")

                with conn.cursor() as cur:
                    with cur.copy(copy_sql) as copy:
                        copy.write(buffer.read())

                conn.commit()

                rows_in_chunk = len(chunk)
                total_rows += rows_in_chunk
                logger.debug(f"Loaded chunk {i}: {rows_in_chunk} rows")

            logger.info(f"PostgreSQL COPY completed: {total_rows} rows loaded")
            return total_rows

        except Exception as e:
            logger.error(f"PostgreSQL COPY failed: {e}")
            raise Exception(f"PostgreSQL COPY failed: {e}") from e
