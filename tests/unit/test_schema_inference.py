import pandas as pd
import pytest
from dataporter.schema.infer_pandas import PandasSchemaInferencer


def test_infer_basic_types():
    """Test schema inference for basic types."""
    # Create sample data
    data = {
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'age': [32, 28, 45, 35, 29],
        'salary': [75000.50, 65000.00, 95000.75, 80000.25, 68000.00],
        'is_active': ['true', 'false', 'true', 'false', 'true'],
    }
    
    df = pd.DataFrame(data)
    chunks = iter([df])
    
    inferencer = PandasSchemaInferencer()
    schema = inferencer.infer('test_table', chunks, sample_chunks=1)
    
    assert len(schema.columns) == 5
    assert schema.get_column('id').inferred_kind == 'int'
    assert schema.get_column('name').inferred_kind == 'string'
    assert schema.get_column('age').inferred_kind == 'int'
    assert schema.get_column('salary').inferred_kind == 'float'
    assert schema.get_column('is_active').inferred_kind == 'bool'


def test_infer_with_nulls():
    """Test schema inference with null values."""
    data = {
        'col1': [1, 2, None, 4, 5],
        'col2': ['a', None, 'c', 'd', 'e'],
    }
    
    df = pd.DataFrame(data)
    chunks = iter([df])
    
    inferencer = PandasSchemaInferencer()
    schema = inferencer.infer('test_table', chunks, sample_chunks=1)
    
    assert schema.get_column('col1').nullable
    assert schema.get_column('col2').nullable


def test_infer_confidence_scoring():
    """Test confidence scoring in type inference."""
    data = {
        'maybe_bool': ['true', 'false', 'maybe', 'yes', 'no'],
        'probably_int': ['1', '2', '3', '4', 'five'],
    }
    
    df = pd.DataFrame(data)
    chunks = iter([df])
    
    inferencer = PandasSchemaInferencer()
    schema = inferencer.infer('test_table', chunks, sample_chunks=1)
    
    # Both should have lower confidence due to anomalies
    maybe_bool_col = schema.get_column('maybe_bool')
    probably_int_col = schema.get_column('probably_int')
    
    assert maybe_bool_col.confidence < 1.0
    assert probably_int_col.confidence < 1.0