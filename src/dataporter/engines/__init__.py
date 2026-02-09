from dataporter.profiles.model import Profile
from dataporter.engines.base import Engine


def create_engine(profile: Profile) -> Engine:
    """
    Factory function to create appropriate engine.
    
    Args:
        profile: Profile object
        
    Returns:
        Engine instance
        
    Raises:
        ValueError: If engine type not supported
    """
    engine_type = profile.engine
    
    if engine_type == 'postgresql':
        from dataporter.engines.postgres import PostgresEngine
        return PostgresEngine(profile)
    
    elif engine_type == 'mysql':
        from dataporter.engines.mysql import MySQLEngine
        return MySQLEngine(profile)
    
    elif engine_type == 'sqlserver':
        from dataporter.engines.sqlserver import SQLServerEngine
        return SQLServerEngine(profile)
    
    elif engine_type == 'bigquery':
        from dataporter.engines.bigquery import BigQueryEngine
        return BigQueryEngine(profile)
    
    else:
        raise ValueError(f"Unsupported engine: {engine_type}")


__all__ = [
    'Engine',
    'create_engine',
]