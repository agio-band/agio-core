from agio.core.settings import collector

__version__ = "0.1.0"
__all__ = ["local_settings", "project_settings"]


local_settings = collector.collect_local_settings()
project_settings = collector.collect_project_settings()
