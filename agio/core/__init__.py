from agio.core import main
from .settings import collector

__version__ = "0.1.0"
__all__ = ["collector"]

settings = collector.collect_local_settings()
