import pytest
from dataporter.schema.mapper import get_db_type, ENGINE_TYPE_MAPS


def test_type_mapping_postgres():
    """Test type mapping for PostgreSQL."""
    assert get_db_type('postgresql', 'int') == 'BIGINT'
    assert get_db_type('postgresql', 'float') == 'DOUBLE PRECISION'
    assert get_db_type('postgresql', 'bool') == 'BOOLEAN'
    assert get_db_type('postgresql', 'datetime') == 'TIMESTAMP'
    assert get_db_type('postgresql', 'string') == 'TEXT'


def test_type_mapping_mysql():
    """Test type mapping for MySQL."""
    assert get_db_type('mysql', 'int') == 'BIGINT'
    assert get_db_type('mysql', 'float') == 'DOUBLE'
    assert get_db_type('mysql', 'bool') == 'TINYINT(1)'
    assert get_db_type('mysql', 'datetime') == 'DATETIME'
    assert get_db_type('mysql', 'string') == 'LONGTEXT'


def test_type_mapping_sqlserver():
    """Test type mapping for SQL Server."""
    assert get_db_type('sqlserver', 'int') == 'BIGINT'
    assert get_db_type('sqlserver', 'float') == 'FLOAT'
    assert get_db_type('sqlserver', 'bool') == 'BIT'
    assert get_db_type('sqlserver', 'datetime') == 'DATETIME2'
    assert get_db_type('sqlserver', 'string') == 'NVARCHAR(MAX)'


def test_type_mapping_bigquery():
    """Test type mapping for BigQuery."""
    assert get_db_type('bigquery', 'int') == 'INT64'
    assert get_db_type('bigquery', 'float') == 'FLOAT64'
    assert get_db_type('bigquery', 'bool') == 'BOOL'
    assert get_db_type('bigquery', 'datetime') == 'TIMESTAMP'
    assert get_db_type('bigquery', 'string') == 'STRING'


def test_unknown_engine():
    """Test error handling for unknown engine."""
    with pytest.raises(ValueError):
        get_db_type('unknown_engine', 'int')


def test_all_engines_have_type_maps():
    """Test that all supported engines have type maps."""
    engines = ['postgresql', 'mysql', 'sqlserver', 'bigquery']
    for engine in engines:
        assert engine in ENGINE_TYPE_MAPS
        assert isinstance(ENGINE_TYPE_MAPS[engine], dict)
        assert len(ENGINE_TYPE_MAPS[engine]) > 0