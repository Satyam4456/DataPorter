from dataporter.loaders.base import LoaderStrategy
from dataporter.loaders.mysql_local_infile import MySQLLocalInfileLoader
from dataporter.loaders.mysql_to_sql import MySQLToSqlLoader
from dataporter.loaders.postgres_copy import PostgresCopyLoader
from dataporter.loaders.sqlserver_bcp import SQLServerBcpLoader
from dataporter.loaders.sqlserver_bulk_insert import SQLServerBulkInsertLoader
from dataporter.loaders.bigquery_load import BigQueryLoadLoader
import logging

logger = logging.getLogger(__name__)


def get_loader(
    engine,
    engine_name: str,
    server_type: str,
) -> LoaderStrategy:
    """
    Get appropriate loader based on engine and server type.
    
    Args:
        engine: Engine instance
        engine_name: Engine name (mysql, postgresql, sqlserver, bigquery)
        server_type: Server type (local or cloud)
    
    Returns:
        LoaderStrategy instance
    """
    
    if engine_name == 'mysql':
        if server_type == 'local':
            return MySQLLocalInfileLoader(engine)
        else:  # cloud
            return MySQLToSqlLoader(engine)
    
    elif engine_name == 'postgresql':
        if server_type == 'local':
            return PostgresCopyLoader(engine)
        else:  # cloud
            return PostgresCopyLoader(engine)
    
    elif engine_name == 'sqlserver':
        if server_type == 'local':
            return SQLServerBulkInsertLoader(engine)
        else:  # cloud
            return SQLServerBcpLoader(engine)
    
    elif engine_name == 'bigquery':
        return BigQueryLoadLoader(engine)
    
    else:
        raise ValueError(f"Unsupported engine: {engine_name}")


__all__ = [
    'LoaderStrategy',
    'MySQLLocalInfileLoader',
    'MySQLToSqlLoader',
    'SQLServerToSqlLoader',
    'PostgresToSqlLoader',
    'BigQueryLoadLoader',
    'get_loader',
]