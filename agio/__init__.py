from agio.core import main
from agio.core.settings.collector import collect_local_settings, collect_workspace_settings

__version__ = "0.0.1"
__all__ = ["local_settings", "workspace_settings"]

local_settings = collect_local_settings()
workspace_settings = collect_workspace_settings()
