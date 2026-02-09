def quote_identifier_postgres(identifier: str) -> str:
    """Quote PostgreSQL identifier."""
    return f'"{identifier}"'


def quote_identifier_mysql(identifier: str) -> str:
    """Quote MySQL identifier."""
    return f'`{identifier}`'


def quote_identifier_sqlserver(identifier: str) -> str:
    """Quote SQL Server identifier."""
    return f'[{identifier}]'


def quote_identifier_bigquery(identifier: str) -> str:
    """Quote BigQuery identifier."""
    return f'`{identifier}`'


def escape_string_postgres(value: str) -> str:
    """Escape string for PostgreSQL."""
    return value.replace("'", "''")


def escape_string_mysql(value: str) -> str:
    """Escape string for MySQL."""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def escape_string_sqlserver(value: str) -> str:
    """Escape string for SQL Server."""
    return value.replace("'", "''")