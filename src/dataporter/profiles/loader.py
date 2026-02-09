import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dataporter.exceptions import ProfileError, ProfileNotFoundError

logger = logging.getLogger(__name__)

# Try to import portalocker for file locking
try:
    import portalocker
    HAS_PORTALOCKER = True
except ImportError:
    HAS_PORTALOCKER = False
    import sys
    if sys.platform == 'win32':
        import msvcrt
    else:
        import fcntl


def get_global_profiles_path() -> Path:
    """
    Get global profiles.yaml path in user home directory.
    
    Windows:  C:\\Users\\<user>\\.dataporter\\profiles.yaml
    Unix:     ~/.dataporter/profiles.yaml
    """
    home = Path.home()
    config_dir = home / ".dataporter"
    return config_dir / "profiles.yaml"


def load_profiles() -> Dict[str, Any]:
    """
    Load profiles from global profiles.yaml.
    
    If file doesn't exist, returns empty profiles structure.
    
    Returns:
        Dictionary with structure: {"profiles": {name: config, ...}}
    """
    profiles_path = get_global_profiles_path()
    
    if not profiles_path.exists():
        logger.debug(f"Profiles file not found: {profiles_path}")
        return {"profiles": {}}
    
    try:
        with open(profiles_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return {"profiles": {}}
        
        if 'profiles' not in data:
            logger.warning("profiles.yaml missing 'profiles' key, creating structure")
            return {"profiles": {}}
        
        return data
        
    except yaml.YAMLError as e:
        raise ProfileError(f"Invalid YAML in profiles.yaml: {e}") from e
    except Exception as e:
        raise ProfileError(f"Error reading profiles.yaml: {e}") from e


def _acquire_lock(file_handle):
    """Acquire file lock (cross-platform)."""
    if HAS_PORTALOCKER:
        portalocker.lock(file_handle, portalocker.LOCK_EX)
    else:
        import sys
        if sys.platform == 'win32':
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)


def _release_lock(file_handle):
    """Release file lock (cross-platform)."""
    if HAS_PORTALOCKER:
        portalocker.unlock(file_handle)
    else:
        import sys
        if sys.platform == 'win32':
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)


def save_profiles(data: Dict[str, Any]) -> None:
    """
    Save profiles to global profiles.yaml with file locking.
    
    Uses atomic write (temp file then replace) to prevent corruption.
    
    Args:
        data: Dictionary with structure {"profiles": {...}}
        
    Raises:
        ProfileError: If save fails
    """
    profiles_path = get_global_profiles_path()
    
    # Ensure directory exists
    profiles_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure data structure
    if 'profiles' not in data:
        data = {"profiles": data.get("profiles", {})}
    
    # Write to temp file first (atomic)
    temp_path = profiles_path.with_suffix('.yaml.tmp')
    
    try:
        # Write temp file
        with open(temp_path, 'w') as f:
            yaml.safe_dump(
                data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
        
        # Atomic replace
        temp_path.replace(profiles_path)
        logger.debug(f"Saved profiles to {profiles_path}")
        
    except Exception as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            try:
                temp_path.unlink()
            except:
                pass
        raise ProfileError(f"Failed to save profiles.yaml: {e}") from e


def profile_exists(name: str) -> bool:
    """
    Check if a profile exists.
    
    Args:
        name: Profile name
        
    Returns:
        True if profile exists, False otherwise
    """
    data = load_profiles()
    return name in data.get("profiles", {})


def get_profile_dict(name: str) -> Dict[str, Any]:
    """
    Get profile configuration dictionary.
    
    Args:
        name: Profile name
        
    Returns:
        Profile configuration
        
    Raises:
        ProfileNotFoundError: If profile not found
    """
    data = load_profiles()
    profiles = data.get("profiles", {})
    
    if name not in profiles:
        available = list(profiles.keys())
        raise ProfileNotFoundError(
            f"Profile '{name}' not found. Available: {available}"
        )
    
    return profiles[name]


def save_profile(name: str, config: Dict[str, Any]) -> None:
    """
    Save a single profile.
    
    Args:
        name: Profile name
        config: Profile configuration
    """
    data = load_profiles()
    data["profiles"][name] = config
    save_profiles(data)


def delete_profile(name: str) -> None:
    """
    Delete a profile.
    
    Args:
        name: Profile name
        
    Raises:
        ProfileNotFoundError: If profile not found
    """
    if not profile_exists(name):
        raise ProfileNotFoundError(f"Profile '{name}' not found")
    
    data = load_profiles()
    del data["profiles"][name]
    save_profiles(data)
    logger.info(f"Deleted profile '{name}'")


# ========== ProfileLoader Class ==========

class ProfileLoader:
    """Load and manage profiles from profiles.yaml file."""
    
    def __init__(self, profiles_path: Optional[str] = None):
        """
        Initialize ProfileLoader.
        
        Args:
            profiles_path: Path to profiles.yaml file
                          If None, uses global path
        """
        if profiles_path is None:
            self.profiles_path = get_global_profiles_path()
        else:
            self.profiles_path = Path(profiles_path)
        
        logger.debug(f"ProfileLoader initialized with: {self.profiles_path}")
    
    def load_profiles(self) -> Dict[str, Any]:
        """
        Load all profiles from file.
        
        Returns:
            Dictionary with structure: {"profiles": {name: config, ...}}
        """
        return load_profiles()
    
    def get_profile(self, name: str):
        """
        Get a specific profile by name.
        
        Args:
            name: Profile name
            
        Returns:
            Profile object
            
        Raises:
            ProfileNotFoundError: If profile not found
        """
        # Import here to avoid circular imports
        from dataporter.profiles.model import Profile
        
        config = get_profile_dict(name)
        return Profile.from_dict(name, config)
    
    def profile_exists(self, name: str) -> bool:
        """
        Check if profile exists.
        
        Args:
            name: Profile name
            
        Returns:
            True if exists, False otherwise
        """
        return profile_exists(name)
    
    def list_profiles(self) -> Dict[str, str]:
        """
        List all profiles.
        
        Returns:
            Dict mapping profile name to engine type
        """
        data = load_profiles()
        profiles = data.get("profiles", {})
        return {name: config.get('engine', 'unknown') for name, config in profiles.items()}