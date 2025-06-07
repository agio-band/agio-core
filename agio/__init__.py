from agio.core import main
from agio.core.settings.collector import collect_local_settings, collect_workspace_settings

local_settings = collect_local_settings()
workspace_settings = collect_workspace_settings()