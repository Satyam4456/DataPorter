from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine as SQLAlchemyEngine
from dataporter.engines.base import Engine
from dataporter.schema.model import TableSchema
from dataporter.exceptions import EngineConnectionError, TableCreationError
from dataporter.utils.quoting import quote_identifier_mysql
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MySQLEngine(Engine):
    """MySQL database engine."""
    
    def __init__(self, profile):
        """
        Initialize MySQL engine.
        
        Args:
            profile: Profile object or dict
        """
        # Handle both Profile objects and dicts
        if hasattr(profile, '__dict__'):
            # It's a Profile object - convert to dict
            self.config = {
                'host': profile.host,
                'port': profile.port,
                'user': profile.user,
                'password': profile.password,
                'database': profile.database,
                'charset': getattr(profile, 'charset', 'utf8mb4'),
            }
        else:
            # It's already a dict
            self.config = profile
        
        self.connection = None
        self._sqlalchemy_engine = None
        
        logger.debug(f"MySQLEngine initialized with config: {self.config}")
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful
        """
        try:
            import pymysql
            
            # Extract config
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 3306)
            user = self.config.get('user', 'root')
            password = self.config.get('password', '')
            database = self.config.get('database', '')
            
            logger.debug(f"Attempting MySQL connection to {user}@{host}:{port}/{database}")
            
            # Connect using keyword arguments (safe for special characters)
            self.connection = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                charset=self.config.get('charset', 'utf8mb4'),
            )
            
            logger.info(f"✓ Connected to MySQL: {user}@{host}:{port}/{database}")
            self.connection.close()
            self.connection = None
            return True
            
        except Exception as e:
            logger.error(f"✗ MySQL connection failed: {e}")
            raise EngineConnectionError(f"MySQL connection failed: {e}") from e
    
    def _get_sqlalchemy_engine(self):
        """
        Get SQLAlchemy engine for this connection.
        
        Returns:
            SQLAlchemy engine with local_infile enabled
        """
        if self._sqlalchemy_engine is None:
            from sqlalchemy import create_engine
            from urllib.parse import quote_plus
            
            # Extract config
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 3306)
            user = self.config.get('user', 'root')
            password = self.config.get('password', '')
            database = self.config.get('database', '')
            charset = self.config.get('charset', 'utf8mb4')
            
            # URL-encode password to handle special characters
            password_encoded = quote_plus(password)
            
            # Build connection string with proper encoding
            connection_string = (
                f"mysql+pymysql://{user}:{password_encoded}@{host}:{port}/{database}"
                f"?charset={charset}"
            )
            
            logger.debug(f"Creating SQLAlchemy engine: mysql+pymysql://{user}:***@{host}:{port}/{database}")
            
            # CRITICAL: Enable local_infile in PyMySQL connection args
            # This allows LOAD DATA LOCAL INFILE to work
            self._sqlalchemy_engine = create_engine(
                connection_string,
                echo=False,
                connect_args={"local_infile": 1}  # Enable LOCAL INFILE
            )
        
        return self._sqlalchemy_engine
    
    def create_table(self, schema: TableSchema, if_exists: str = "fail") -> None:
        """Create table in MySQL."""
        table_name = schema.table_name
        
        # Check if exists
        exists = self.table_exists(table_name)
        
        if exists:
            if if_exists == 'fail':
                raise TableCreationError(f"Table {table_name} already exists")
            elif if_exists == 'replace':
                self.drop_table(table_name)
            elif if_exists == 'append':
                logger.info(f"Table {table_name} exists, will append data")
                return
        
        # Build CREATE TABLE statement
        columns_sql = []
        for col in schema.columns:
            col_name = quote_identifier_mysql(col.name)
            col_type = col.db_types.get('mysql', 'LONGTEXT')
            nullable = 'NULL' if col.nullable else 'NOT NULL'
            columns_sql.append(f"{col_name} {col_type} {nullable}")
        
        columns_clause = ',\n  '.join(columns_sql)
        table_qualified = quote_identifier_mysql(table_name)
        
        create_sql = f"""
        CREATE TABLE {table_qualified} (
          {columns_clause}
        )
        """
        
        engine = self._get_sqlalchemy_engine()
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
        """Drop table from MySQL."""
        engine = self._get_sqlalchemy_engine()
        with engine.connect() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
            conn.commit()
        logger.info(f"Dropped table {table_name}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("MySQL connection closed")
        
        if self._sqlalchemy_engine:
            self._sqlalchemy_engine.dispose()
            logger.info("SQLAlchemy engine disposed")