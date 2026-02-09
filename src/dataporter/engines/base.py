from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataporter.schema.model import TableSchema
from dataporter.profiles.model import Profile
import logging

logger = logging.getLogger(__name__)


class Engine(ABC):
    """Base class for database engines."""
    
    engine_name: str = ""
    
    def __init__(self, profile: Profile):
        """
        Initialize engine with profile.
        
        Args:
            profile: Connection profile
        """
        self.profile = profile
        self.config = profile.get_config()
        self.connection = None
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to database.
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def create_table(
        self,
        schema: TableSchema,
        if_exists: str = 'fail',
    ) -> None:
        """
        Create table based on schema.
        
        Args:
            schema: TableSchema object
            if_exists: 'fail', 'replace', or 'append'
        """
        pass
    
    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        pass
    
    @abstractmethod
    def drop_table(self, table_name: str) -> None:
        """Drop table if exists."""
        pass
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None