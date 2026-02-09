import pytest
from dataporter.loaders import get_loader
from dataporter.loaders.postgres_copy import PostgresCopyLoader
from dataporter.loaders.mysql_local_infile import MySQLLocalInfileLoader
from dataporter.loaders.mysql_to_sql import MySQLToSqlLoader
from dataporter.loaders.sqlserver_bcp import SQLServerBcpLoader
from dataporter.loaders.sqlserver_bulk_insert import SQLServerBulkInsertLoader
from dataporter.loaders.bigquery_load import BigQueryLoadLoader
from unittest.mock import Mock


def test_postgres_loader_selection():
    """Test PostgreSQL loader selection (always COPY)."""
    mock_engine = Mock()
    
    # Local
    loader = get_loader(mock_engine, 'postgresql', 'local')
    assert isinstance(loader, PostgresCopyLoader)
    
    # Cloud
    loader = get_loader(mock_engine, 'postgresql', 'cloud')
    assert isinstance(loader, PostgresCopyLoader)


def test_mysql_loader_selection():
    """Test MySQL loader selection (depends on server_type)."""
    mock_engine = Mock()
    
    # Local → LOAD DATA LOCAL INFILE
    loader = get_loader(mock_engine, 'mysql', 'local')
    assert isinstance(loader, MySQLLocalInfileLoader)
    
    # Cloud → to_sql
    loader = get_loader(mock_engine, 'mysql', 'cloud')
    assert isinstance(loader, MySQLToSqlLoader)


def test_sqlserver_loader_selection():
    """Test SQL Server loader selection (depends on server_type)."""
    mock_engine = Mock()
    
    # Local → BULK INSERT
    loader = get_loader(mock_engine, 'sqlserver', 'local')
    assert isinstance(loader, SQLServerBulkInsertLoader)
    
    # Cloud → BCP
    loader = get_loader(mock_engine, 'sqlserver', 'cloud')
    assert isinstance(loader, SQLServerBcpLoader)


def test_bigquery_loader_selection():
    """Test BigQuery loader selection (always GCS URI)."""
    mock_engine = Mock()
    
    # Only GCS URI supported
    loader = get_loader(mock_engine, 'bigquery', 'cloud')
    assert isinstance(loader, BigQueryLoadLoader)


def test_invalid_engine():
    """Test error handling for unknown engine."""
    mock_engine = Mock()
    
    with pytest.raises(ValueError):
        get_loader(mock_engine, 'unknown_engine', 'local')