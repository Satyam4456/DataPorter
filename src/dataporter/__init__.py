"""
DataPorter - Simple data ingestion tool for multiple database engines.
"""

__version__ = "0.1.0"

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    """Lazy load DataPorter class on demand."""
    if name == "DataPorter":
        from dataporter.api import DataPorter
        return DataPorter
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__():
    return ["DataPorter", "__version__"]