from sqlalchemy import create_engine, inspect, text
from dataporter.engines.base import Engine
from dataporter.schema.model import TableSchema
from dataporter.exceptions import EngineConnectionError
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)


class SQLServerEngine(Engine):
    """SQL Server database engine."""
    
    def __init__(self, profile):
        """Initialize SQL Server engine."""
        if hasattr(profile, '__dict__'):
            self.config = {
                'host': profile.host,
                'port': profile.port,
                'user': profile.user,
                'password': profile.password,
                'database': profile.database,
            }
        else:
            self.config = profile
        
        self._sqlalchemy_engine = None
        logger.debug(f"SQLServerEngine initialized")
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            engine = self._get_sqlalchemy_engine()
            with engine.connect() as conn:
                logger.info("SQL Server connection successful")
            return True
        except Exception as e:
            logger.error(f"SQL Server connection failed: {e}")
            raise EngineConnectionError(f"SQL Server connection failed: {e}") from e
    
    def _get_sqlalchemy_engine(self):
        """Get SQLAlchemy engine with proper connection string."""
        if self._sqlalchemy_engine is None:
            host = self.config.get('host', 'localhost')
            user = self.config.get('user', 'sa')
            password = self.config.get('password', '')
            database = self.config.get('database', 'master')
            
            # 1. Handle LocalDB connection strings
            # If host starts with (localdb), we MUST NOT include a port
            if "(localdb)" in host.lower():
                server_spec = host
            else:
                port = self.config.get('port', 1433)
                server_spec = f"{host},{port}"

            # URL-encode password to handle special characters
            password_encoded = quote_plus(password)
            
            # Build connection string properly
            # Format: mssql+pyodbc://username:password@host:port/database?driver=ODBC+Driver+18+for+SQL+Server
            connection_string = (
                f"mssql+pyodbc://{user}:{password_encoded}@{server_spec}/{database}"
                f"?driver=ODBC+Driver+18+for+SQL+Server"
                f"&TrustServerCertificate=yes&Encrypt=no"
            )
            
            logger.debug(f"Creating SQLAlchemy engine for SQL Server")
            self._sqlalchemy_engine = create_engine(connection_string, echo=False)
        
        return self._sqlalchemy_engine
    
    def create_table(self, schema: TableSchema, if_exists: str = "fail") -> None:
        """Create table in SQL Server."""
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
        
        # Build CREATE TABLE statement
        columns_sql = []
        for col in schema.columns:
            col_name = f"[{col.name}]"
            
            if col.inferred_kind == 'int':
                col_type = "BIGINT"
            elif col.inferred_kind == 'float':
                col_type = "FLOAT"
            elif col.inferred_kind == 'bool':
                col_type = "BIT"
            elif col.inferred_kind == 'datetime':
                if 'time' in col.name.lower() and 'date' not in col.name.lower():
                    col_type = "TIME"
                else:
                    col_type = "DATETIME2"
            else:
                col_type = "NVARCHAR(MAX)"
            
            nullable = "NULL" if col.nullable else "NOT NULL"
            columns_sql.append(f"{col_name} {col_type} {nullable}")
        
        columns_clause = ',\n  '.join(columns_sql)
        create_sql = f"CREATE TABLE [{table_name}] (\n  {columns_clause}\n)"
        
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
            conn.execute(text(f"DROP TABLE IF EXISTS [{table_name}]"))
            conn.commit()
        logger.info(f"Dropped table {table_name}")
    
    def close(self) -> None:
        """Close connection."""
        if self._sqlalchemy_engine:
            self._sqlalchemy_engine.dispose()
            logger.info("SQL Server engine disposed")