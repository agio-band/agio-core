from .package import APackageManager
from .package_repostory import APackageRepository
from .workspace import AWorkspaceManager
from agio.core.settings import collector
from agio.core import entities


def sync_current_workspace():
    """
    Save current workspace settings layout to db
    """
    rev = entities.AWorkspace.current().get_manager().revision
    if not rev:
        raise ValueError('Current workspace revision not defined')
    settings_layout = collector.collect_workspace_settings_layout()
    rev.set_layout(settings_layout)
