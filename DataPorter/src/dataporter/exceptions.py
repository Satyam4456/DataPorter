class DataPorterError(Exception):
    """Base exception for DataPorter."""
    pass


class ProfileError(DataPorterError):
    """Raised when profile configuration is invalid."""
    pass


class ProfileNotFoundError(ProfileError):
    """Raised when profile name not found."""
    pass


class ProfileExistsError(ProfileError):
    """Raised when trying to create profile that already exists."""
    pass


class SchemaInferenceError(DataPorterError):
    """Raised when schema inference fails."""
    pass


class EngineConnectionError(DataPorterError):
    """Raised when engine connection fails."""
    pass


class TableCreationError(DataPorterError):
    """Raised when table creation fails."""
    pass


class DataLoadError(DataPorterError):
    """Raised when data loading fails."""
    pass


class ReaderError(DataPorterError):
    """Raised when file reading fails."""
    pass


class LoaderStrategyError(DataPorterError):
    """Raised when loader selection/execution fails."""
    pass


class TypeMappingError(DataPorterError):
    """Raised when type mapping fails."""
    pass