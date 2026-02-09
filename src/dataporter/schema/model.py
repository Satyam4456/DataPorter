from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class ColumnSchema:
    """Schema for a single column."""
    name: str
    inferred_kind: str  # 'int', 'float', 'bool', 'datetime', 'string'
    nullable: bool = True
    pandas_dtype: str = 'object'
    confidence: float = 1.0
    db_types: Dict[str, str] = field(default_factory=dict)  # engine -> db_type
    sample_values: List[Any] = field(default_factory=list)
    
    def get_db_type(self, engine: str) -> str:
        """Get database-specific type for engine."""
        return self.db_types.get(engine, 'VARCHAR(255)')


@dataclass
class TableSchema:
    """Schema for a table."""
    table_name: str
    columns: List[ColumnSchema] = field(default_factory=list)
    inferred_at: Optional[str] = None
    
    def get_column(self, name: str) -> Optional[ColumnSchema]:
        """Get column schema by name."""
        for col in self.columns:
            if col.name.lower() == name.lower():
                return col
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'table_name': self.table_name,
            'columns': [
                {
                    'name': col.name,
                    'kind': col.inferred_kind,
                    'nullable': col.nullable,
                    'confidence': col.confidence,
                    'sample_values': col.sample_values,
                }
                for col in self.columns
            ],
            'inferred_at': self.inferred_at,
        }