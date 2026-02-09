import logging
import sys


def configure_logging(level=logging.INFO):
    """Configure standard logging for DataPorter."""
    logger = logging.getLogger('dataporter')
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    logger.setLevel(level)
    
    # Only add handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.propagate = False  # Prevent propagation to root logger
    
    return logger