from typing import Dict

# Type mapping from inferred kind to database types

POSTGRES_TYPE_MAP: Dict[str, str] = {
    'int': 'BIGINT',
    'float': 'DOUBLE PRECISION',
    'bool': 'BOOLEAN',
    'datetime': 'TIMESTAMP',
    'time': 'TIME',
    'string': 'TEXT',
}

MYSQL_TYPE_MAP: Dict[str, str] = {
    'int': 'BIGINT',
    'float': 'DOUBLE',
    'bool': 'TINYINT(1)',
    'datetime': 'DATETIME',
    'string': 'LONGTEXT',
}

SQLSERVER_TYPE_MAP: Dict[str, str] = {
    'int': 'BIGINT',
    'float': 'FLOAT',
    'bool': 'BIT',
    'datetime': 'DATETIME2',
    'string': 'NVARCHAR(MAX)',
}

BIGQUERY_TYPE_MAP: Dict[str, str] = {
    'int': 'INT64',
    'float': 'FLOAT64',
    'bool': 'BOOL',
    'datetime': 'TIMESTAMP',
    'string': 'STRING',
}

ENGINE_TYPE_MAPS: Dict[str, Dict[str, str]] = {
    'postgresql': POSTGRES_TYPE_MAP,
    'mysql': MYSQL_TYPE_MAP,
    'sqlserver': SQLSERVER_TYPE_MAP,
    'bigquery': BIGQUERY_TYPE_MAP,
}


def get_db_type(engine: str, inferred_kind: str) -> str:
    """
    Get database-specific type from inferred kind.
    
    Args:
        engine: Engine name (postgresql, mysql, sqlserver, bigquery)
        inferred_kind: Inferred kind (int, float, bool, datetime, string)
        
    Returns:
        Database-specific type string
    """
    type_map = ENGINE_TYPE_MAPS.get(engine)
    if not type_map:
        raise ValueError(f"Unknown engine: {engine}")
    
    db_type = type_map.get(inferred_kind, 'VARCHAR(255)')
    return db_type