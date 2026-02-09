from typing import Dict, List, Optional
from dataporter.schema.model import TableSchema, ColumnSchema
from dataporter.schema.mapper import get_db_type
import logging

logger = logging.getLogger(__name__)


class SchemaOverrideManager:
    """Manage user overrides for schema inference."""
    
    def __init__(self, schema: TableSchema):
        """
        Initialize override manager.
        
        Args:
            schema: Initial TableSchema
        """
        self.schema = schema
        self.overrides: Dict[str, str] = {}
    
    def apply_overrides(self, overrides: Dict[str, str], engine: str) -> TableSchema:
        """
        Apply type overrides to schema.
        
        Args:
            overrides: Dict mapping column_name -> inferred_kind
            engine: Engine name for type mapping
            
        Returns:
            Modified TableSchema
        """
        for col_name, kind in overrides.items():
            col = self.schema.get_column(col_name)
            if not col:
                logger.warning(f"Column '{col_name}' not found in schema")
                continue
            
            if kind not in ('int', 'float', 'bool', 'datetime', 'string'):
                logger.warning(f"Unknown kind '{kind}' for column '{col_name}'")
                continue
            
            # Update column
            col.inferred_kind = kind
            col.confidence = 1.0  # User override = high confidence
            col.db_types[engine] = get_db_type(engine, kind)
            logger.info(f"Override column '{col_name}' to type '{kind}'")
        
        return self.schema
    
    def get_uncertain_columns(
        self,
        confidence_threshold: float = 0.85,
    ) -> List[ColumnSchema]:
        """
        Get columns with confidence below threshold.
        
        Args:
            confidence_threshold: Confidence threshold
            
        Returns:
            List of uncertain ColumnSchema objects
        """
        return [
            col for col in self.schema.columns
            if col.confidence < confidence_threshold
        ]
    
    def interactive_override(self, engine: str) -> None:
        """
        Interactively ask user to override uncertain columns.
        
        Args:
            engine: Engine name for type mapping
        """
        uncertain = self.get_uncertain_columns()
        
        if not uncertain:
            logger.info("No uncertain columns detected")
            return
        
        logger.info(f"Found {len(uncertain)} uncertain column(s)")
        
        for col in uncertain:
            print(f"\nColumn: {col.name}")
            print(f"  Inferred type: {col.inferred_kind} (confidence: {col.confidence:.2f})")
            print(f"  Sample values: {col.sample_values}")
            print(f"  Options: int, float, bool, datetime, string")
            
            user_input = input(f"  Override type (or press Enter to keep): ").strip().lower()
            
            if user_input in ('int', 'float', 'bool', 'datetime', 'string'):
                col.inferred_kind = user_input
                col.confidence = 1.0
                col.db_types[engine] = get_db_type(engine, user_input)
                logger.info(f"Column '{col.name}' overridden to '{user_input}'")