import time
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class Timer:
    """Simple timer utility."""
    
    def __init__(self, label: str = ""):
        """Initialize timer."""
        self.label = label
        self.start_time = None
        self.end_time = None
    
    def start(self) -> None:
        """Start timer."""
        self.start_time = time.time()
    
    def stop(self) -> float:
        """Stop timer and return elapsed seconds."""
        self.end_time = time.time()
        return self.elapsed
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def __str__(self) -> str:
        """String representation."""
        elapsed = self.elapsed
        return f"{self.label}: {elapsed:.2f}s"


@contextmanager
def timer(label: str = "Operation"):
    """Context manager for timing operations."""
    t = Timer(label)
    t.start()
    try:
        yield t
    finally:
        t.stop()
        logger.info(str(t))