from typing import Dict, Optional
from dataporter.profiles.model import Profile
from dataporter.profiles.validators import validate_profile_dict
import os
import yaml
import logging

logger = logging.getLogger(__name__)

# Profile file location
PROFILES_FILE = r'd:\Python\Dataporter_venv\Data import project\DataPorter\profiles.yaml'


def _save_profile(name: str, profile: Profile):
    """Save profile to profiles.yaml file."""
    
    # Load existing profiles
    data = {}
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, 'r') as f:
            data = yaml.safe_load(f) or {}
    
    # Ensure profiles key exists
    if 'profiles' not in data:
        data['profiles'] = {}
    
    # Build profile data
    if profile.engine == 'bigquery':
        profile_data = {
            'engine': profile.engine,
            'project_id': profile.project_id,
            'dataset': profile.dataset,
            'credentials_path': profile.credentials_path,
        }
    else:
        profile_data = {
            'engine': profile.engine,
            'host': profile.host,
            'port': profile.port,
            'user': profile.user,
            'password': profile.password,
            'database': profile.database,
        }
    
    # Add/update profile under profiles key
    data['profiles'][name] = profile_data
    
    # Save to YAML
    with open(PROFILES_FILE, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    
    logger.debug(f"Saved profile: {name} to {PROFILES_FILE}")


def _load_profile(name: str) -> Optional[Profile]:
    """Load profile from profiles.yaml file."""
    if not os.path.exists(PROFILES_FILE):
        return None
    
    with open(PROFILES_FILE, 'r') as f:
        data = yaml.safe_load(f) or {}
    
    # Get profiles from under 'profiles' key
    profiles_data = data.get('profiles', {})
    
    if name not in profiles_data:
        return None
    
    profile_data = profiles_data[name]
    engine = profile_data.get('engine')
    
    if engine == 'bigquery':
        profile = Profile(
            name=name,
            engine=engine,
            project_id=profile_data.get('project_id'),
            dataset=profile_data.get('dataset'),
            credentials_path=profile_data.get('credentials_path'),
        )
    else:
        profile = Profile(
            name=name,
            engine=engine,
            host=profile_data.get('host'),
            port=profile_data.get('port'),
            user=profile_data.get('user'),
            password=profile_data.get('password'),
            database=profile_data.get('database'),
        )
    
    logger.debug(f"Loaded profile: {name}")
    return profile


def create_profile(
    name: str,
    engine: str,
    **kwargs
) -> Profile:
    """Create a new profile."""
    
    # Validate first
    validate_profile_dict(engine, kwargs)
    
    if engine == 'mysql':
        profile = Profile(
            name=name,
            engine=engine,
            host=kwargs.get('host', 'localhost'),
            port=kwargs.get('port', 3306),
            user=kwargs.get('user'),
            password=kwargs.get('password'),
            database=kwargs.get('database'),
        )
    
    elif engine == 'postgresql':
        profile = Profile(
            name=name,
            engine=engine,
            host=kwargs.get('host', 'localhost'),
            port=kwargs.get('port', 5432),
            user=kwargs.get('user'),
            password=kwargs.get('password'),
            database=kwargs.get('database'),
        )
    
    elif engine == 'sqlserver':
        profile = Profile(
            name=name,
            engine=engine,
            host=kwargs.get('host'),
            port=kwargs.get('port', 1433),
            user=kwargs.get('user'),
            password=kwargs.get('password'),
            database=kwargs.get('database'),
        )
    
    elif engine == 'bigquery':
        profile = Profile(
            name=name,
            engine=engine,
            project_id=kwargs.get('project_id'),
            dataset=kwargs.get('dataset'),
            credentials_path=kwargs.get('credentials_path'),
        )
    
    else:
        raise ValueError(f"Unsupported engine: {engine}")
    
    _save_profile(name, profile)
    logger.info(f"Created profile: {name}")
    return profile


def get_profile(name: str) -> Optional[Profile]:
    """Get profile by name."""
    return _load_profile(name)


def list_profiles() -> Dict[str, str]:
    """List all available profiles."""
    if not os.path.exists(PROFILES_FILE):
        return {}
    
    with open(PROFILES_FILE, 'r') as f:
        data = yaml.safe_load(f) or {}
    
    # Get profiles from under 'profiles' key
    profiles_data = data.get('profiles', {})
    
    profiles = {}
    for name, profile_data in profiles_data.items():
        profiles[name] = profile_data.get('engine', 'unknown')
    
    return profiles


def delete_profile(name: str) -> bool:
    """Delete a profile."""
    if not os.path.exists(PROFILES_FILE):
        return False
    
    with open(PROFILES_FILE, 'r') as f:
        data = yaml.safe_load(f) or {}
    
    # Get profiles from under 'profiles' key
    profiles_data = data.get('profiles', {})
    
    if name not in profiles_data:
        return False
    
    del profiles_data[name]
    data['profiles'] = profiles_data
    
    with open(PROFILES_FILE, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    
    logger.info(f"Deleted profile: {name}")
    return True


def get_profile_fields(engine: str) -> dict:
    """Get required fields for engine."""
    if engine == 'bigquery':
        return {
            'required': ['project_id', 'dataset', 'credentials_path'],
            'prompts': {
                'project_id': 'Google Cloud Project ID (e.g., my-project-123)',
                'dataset': 'BigQuery Dataset ID (e.g., my_dataset)',
                'credentials_path': 'Path to service account JSON key file (e.g., /path/to/key.json)',
            }
        }
    
    elif engine == 'mysql':
        return {
            'required': ['host', 'port', 'user', 'password', 'database'],
            'prompts': {
                'host': 'MySQL host (default: localhost)',
                'port': 'MySQL port (default: 3306)',
                'user': 'MySQL username',
                'password': 'MySQL password',
                'database': 'Database name',
            }
        }
    
    elif engine == 'postgresql':
        return {
            'required': ['host', 'port', 'user', 'password', 'database'],
            'prompts': {
                'host': 'PostgreSQL host',
                'port': 'PostgreSQL port (default: 5432)',
                'user': 'PostgreSQL username',
                'password': 'PostgreSQL password',
                'database': 'Database name',
            }
        }
    
    elif engine == 'sqlserver':
        return {
            'required': ['host', 'port', 'user', 'password', 'database'],
            'prompts': {
                'host': 'SQL Server host',
                'port': 'SQL Server port (default: 1433)',
                'user': 'SQL Server username',
                'password': 'SQL Server password',
                'database': 'Database name',
            }
        }
    
    else:
        raise ValueError(f"Unsupported engine: {engine}")