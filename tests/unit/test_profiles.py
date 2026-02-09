import pytest
import tempfile
import yaml
from pathlib import Path

from dataporter.profiles.loader import ProfileLoader
from dataporter.exceptions import ProfileError, ProfileNotFoundError


def test_load_valid_profiles():
    """Test loading valid profiles from YAML."""
    profile_data = {
        'profiles': {
            'test_pg': {
                'engine': 'postgresql',
                'host': 'localhost',
                'user': 'test',
                'password': 'test',
                'database': 'testdb',
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(profile_data, f)
        f.flush()
        
        loader = ProfileLoader(f.name)
        profile = loader.get_profile('test_pg')
        
        assert profile.name == 'test_pg'
        assert profile.engine == 'postgresql'
        assert profile.config['host'] == 'localhost'
        
        Path(f.name).unlink()


def test_profile_not_found():
    """Test error when profile doesn't exist."""
    profile_data = {
        'profiles': {
            'test_pg': {
                'engine': 'postgresql',
                'host': 'localhost',
                'user': 'test',
                'password': 'test',
                'database': 'testdb',
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(profile_data, f)
        f.flush()
        
        loader = ProfileLoader(f.name)
        
        with pytest.raises(ProfileNotFoundError):
            loader.get_profile('nonexistent')
        
        Path(f.name).unlink()


def test_missing_required_field():
    """Test validation of missing required fields."""
    profile_data = {
        'profiles': {
            'invalid_pg': {
                'engine': 'postgresql',
                # Missing required fields
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(profile_data, f)
        f.flush()
        
        with pytest.raises(ProfileError):
            ProfileLoader(f.name)
        
        Path(f.name).unlink()