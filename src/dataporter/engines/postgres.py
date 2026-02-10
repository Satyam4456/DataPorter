from sqlalchemy import create_engine, inspect, text
from dataporter.engines.base import Engine
from dataporter.schema.model import TableSchema
from dataporter.exceptions import EngineConnectionError
import logging

logger = logging.getLogger(__name__)


class PostgresEngine(Engine):
    """PostgreSQL database engine."""
    
    def __init__(self, profile):
        """Initialize PostgreSQL engine."""
        if hasattr(profile, '__dict__'):
            self.config = {
                'host': profile.host,
                'port': profile.port,
                'user': profile.user,
                'password': profile.password,
                'database': profile.database,
                'schema': getattr(profile, 'schema', 'public'),
            }
        else:
            self.config = profile
        
        self.connection = None
        self._sqlalchemy_engine = None
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            import psycopg
            
            conn = psycopg.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                user=self.config.get('user', 'postgres'),
                password=self.config.get('password', ''),
                dbname=self.config.get('database', '')
            )

            conn.close()
            logger.info("PostgreSQL connection successful")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise EngineConnectionError(f"PostgreSQL connection failed: {e}") from e
    
    def _get_connection(self):
        """
        Ensures the 'connection' attribute is populated and returned.
        """
        if getattr(self, 'connection', None) is None:
            import psycopg

            self.connection = psycopg.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                user=self.config.get('user', 'postgres'),
                password=self.config.get('password', ''),
                dbname=self.config.get('database', '')
            )
        return self.connection
    
    def _get_sqlalchemy_engine(self):
        """Get SQLAlchemy engine."""
        if self._sqlalchemy_engine is None:
            from sqlalchemy import create_engine
            from urllib.parse import quote_plus
            
            password_encoded = quote_plus(self.config.get('password', ''))
            
            connection_string = (
                f"postgresql+psycopg://{self.config.get('user', 'postgres')}:{password_encoded}"
                f"@{self.config.get('host', 'localhost')}:{self.config.get('port', 5432)}"
                f"/{self.config.get('database', '')}"
            )
            
            self._sqlalchemy_engine = create_engine(connection_string, echo=False)
        
        return self._sqlalchemy_engine
    
    def create_table(self, schema: TableSchema, if_exists: str = "fail") -> None:
        """Create table in PostgreSQL."""
        table_name = schema.table_name
        engine = self._get_sqlalchemy_engine()
        
        exists = self.table_exists(table_name)
        
        if exists:
            if if_exists == 'fail':
                raise Exception(f"Table {table_name} already exists")
            elif if_exists == 'replace':
                self.drop_table(table_name)
            elif if_exists == 'append':
                logger.info(f"Table {table_name} exists, will append data")
                return
        
        # Build CREATE TABLE statement with proper types
        columns_sql = []
        for col in schema.columns:
            col_name = f'"{col.name}"'
            
            if col.inferred_kind == 'int':
                col_type = "BIGINT"
            elif col.inferred_kind == 'float':
                col_type = "DOUBLE PRECISION"
            elif col.inferred_kind == 'bool':
                col_type = "BOOLEAN"
            elif col.inferred_kind == 'datetime':
                # Check if column is time-only (not datetime)
                if 'time' in col.name.lower() and 'date' not in col.name.lower():
                    col_type = "TIME"
                else:
                    col_type = "TIMESTAMP"
            else:
                col_type = "TEXT"
            
            nullable = "NULL" if col.nullable else "NOT NULL"
            columns_sql.append(f"{col_name} {col_type} {nullable}")
        
        columns_clause = ',\n  '.join(columns_sql)
        create_sql = f'CREATE TABLE "{table_name}" (\n  {columns_clause}\n)'
        
        with engine.connect() as conn:
            conn.execute(text(create_sql))
            conn.commit()
        
        logger.info(f"Created table {table_name}")
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        engine = self._get_sqlalchemy_engine()
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()
    
    def drop_table(self, table_name: str) -> None:
        """Drop table."""
        engine = self._get_sqlalchemy_engine()
        with engine.connect() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
            conn.commit()
        logger.info(f"Dropped table {table_name}")
    
    def close(self) -> None:
        """Close connection."""
        if self.connection is not None:
            try:
                if not self.connection.closed:
                    self.connection.close()
                    logger.info("PostgreSQL connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            finally:
                self.connection = None
        
        if self._sqlalchemy_engine:
            self._sqlalchemy_engine.dispose()
            logger.info("SQLAlchemy engine disposed")