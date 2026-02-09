from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any


@dataclass
class Profile:
    """Generic profile for database connections."""
    name: str
    engine: str
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    driver: Optional[str] = None
    project_id: Optional[str] = None
    dataset: Optional[str] = None
    gcs_bucket: Optional[str] = None
    gcs_prefix: Optional[str] = None
    credentials_path: Optional[str] = None
    charset: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values and name."""
        data = asdict(self)
        data.pop('name', None)  # Remove name from dict (stored as key in YAML)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "Profile":
        """Create Profile from dictionary."""
        data_with_name = {'name': name, **data}
        # Filter to only valid fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data_with_name.items() if k in valid_fields}
        return cls(**filtered)
    
    def get_config(self) -> Dict[str, Any]:
        """Return configuration dictionary for engines."""
        return self.to_dict()