import re
import os
import logging
from typing import Dict, Any
from dataporter.exceptions import ProfileError


VALID_ENGINES = ('postgresql', 'mysql', 'sqlserver', 'bigquery')
PROFILE_NAME_PATTERN = r'^[a-zA-Z0-9_]+$'
logger = logging.getLogger(__name__)


def validate_profile_name(name: str) -> None:
    """
    Validate profile name format.
    
    Args:
        name: Profile name
        
    Raises:
        ProfileError: If name is invalid
    """
    if not name:
        raise ProfileError("Profile name cannot be empty")
    
    if not re.match(PROFILE_NAME_PATTERN, name):
        raise ProfileError(
            f"Profile name '{name}' must be alphanumeric with underscores only"
        )


def validate_engine(engine: str) -> None:
    """
    Validate engine name.
    
    Args:
        engine: Engine name
        
    Raises:
        ProfileError: If engine is invalid
    """
    if engine not in VALID_ENGINES:
        raise ProfileError(
            f"Engine '{engine}' not supported. "
            f"Must be one of: {', '.join(VALID_ENGINES)}"
        )


def validate_port(port: Any) -> None:
    """
    Validate port number.
    
    Args:
        port: Port number
        
    Raises:
        ProfileError: If port is invalid
    """
    if port is None:
        return  # Port is optional with defaults
    
    try:
        port_int = int(port)
        if port_int < 1 or port_int > 65535:
            raise ValueError
    except (ValueError, TypeError):
        raise ProfileError(f"Port must be an integer between 1 and 65535, got {port}")


def validate_mysql_profile(config: dict) -> bool:
    """Validate MySQL profile."""
    required = ['host', 'port', 'user', 'password', 'database']
    missing = [k for k in required if not config.get(k)]
    if missing:
        raise ValueError(f"MySQL profile missing required fields: {missing}")
    return True


def validate_postgresql_profile(config: dict) -> bool:
    """Validate PostgreSQL profile."""
    required = ['host', 'port', 'user', 'password', 'database']
    missing = [k for k in required if not config.get(k)]
    if missing:
        raise ValueError(f"PostgreSQL profile missing required fields: {missing}")
    return True


def validate_sqlserver_profile(config: dict) -> bool:
    """Validate SQL Server profile."""
    required = ['host', 'port', 'user', 'password', 'database']
    missing = [k for k in required if not config.get(k)]
    if missing:
        raise ValueError(f"SQL Server profile missing required fields: {missing}")
    return True


def validate_bigquery_profile(config: dict) -> bool:
    """Validate BigQuery profile."""
    required = ['project_id', 'dataset', 'credentials_path']
    
    missing = [k for k in required if not config.get(k)]
    if missing:
        raise ValueError(f"BigQuery profile missing required fields: {missing}")
    
    # Validate credentials file exists
    creds_path = config.get('credentials_path')
    if creds_path and not os.path.exists(creds_path):
        raise ValueError(f"Credentials file not found: {creds_path}")
    
    return True


def normalize_profile_dict(engine: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize profile configuration with defaults.
    
    Args:
        engine: Engine name
        config: Profile configuration
        
    Returns:
        Normalized configuration
    """
    normalized = dict(config)
    
    if engine == 'postgresql':
        normalized.setdefault('port', 5432)
        normalized.setdefault('schema', 'public')
    
    elif engine == 'mysql':
        normalized.setdefault('port', 3306)
        normalized.setdefault('charset', 'utf8mb4')
    
    elif engine == 'sqlserver':
        normalized.setdefault('port', 1433)
        normalized.setdefault('driver', 'ODBC Driver 18 for SQL Server')
        normalized.setdefault('schema', 'dbo')
    
    elif engine == 'bigquery':
        normalized.setdefault('gcs_prefix', 'dataporter_uploads/')
    
    return normalized


def validate_profile_dict(engine: str, config: Dict[str, Any]) -> None:
    """
    Validate profile configuration.
    
    Args:
        engine: Engine name
        config: Profile configuration
        
    Raises:
        ProfileError: If validation fails
    """
    validate_engine(engine)
    
    if engine == 'postgresql':
        validate_postgresql_profile(config)
    
    elif engine == 'mysql':
        validate_mysql_profile(config)
    
    elif engine == 'sqlserver':
        validate_sqlserver_profile(config)
    
    elif engine == 'bigquery':
        validate_bigquery_profile(config)