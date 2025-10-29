from __future__ import annotations
import json
import logging
import os
from pathlib import Path

from agio.core.entities import project as pd
from agio.core.events import emit
from agio.tools import app_dirs
from agio.tools.json_serializer import JsonSerializer
from agio.core.settings import settings_hub

logger = logging.getLogger(__name__)

_settings_dir = Path(os.getenv('AGIO_SETTINGS_DIR') or app_dirs.projects_settings_dir())
_settings_file_name = 'settings.json'


def get_settings_dir(project_id: str = None):
    return _settings_dir.joinpath(project_id)


def get_project_dir_name(project: str | pd.AProject = None):
    if isinstance(project, pd.AProject):
        return str(project.id)
    else:
        return 'default'


def load_default_settings():
    settings_file = Path(get_settings_dir(get_project_dir_name(None)), _settings_file_name)
    if not settings_file.is_file():
        emit('core.settings.default_not_exists')
        return {}
    default_settings = json.loads(settings_file.read_text(encoding='utf-8'))
    emit('core.settings.default_settings_loaded', {'settings': default_settings})
    return default_settings


def load(project: str | pd.AProject = None) -> settings_hub.LocalSettingsHub:
    if project:
        settings_data = load_default_settings()
    else:
        settings_data = {}
    settings_file = Path(get_settings_dir(get_project_dir_name(project)), _settings_file_name)
    if settings_file.exists():
        settings_data.update(json.loads(settings_file.read_text(encoding='utf-8')))
    settings = settings_hub.LocalSettingsHub(settings_data)
    emit('core.settings.project_settings_loaded', {'settings': settings, 'project': project})
    logger.debug(f'Loaded settings from {settings_file}')
    return settings


def save(settings: settings_hub.LocalSettingsHub, project: str | pd.AProject=None) -> str:
    settings_file = Path(get_settings_dir(get_project_dir_name(project)), _settings_file_name)
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    emit('core.settings.before_project_settings_save', {'settings': settings, 'project': project})
    settings_file.write_text(json.dumps(settings.dump(), indent=2, cls=JsonSerializer))
    emit('core.settings.project_settings_saved', {'settings': settings, 'project': project, 'file': settings_file})
    logger.debug(f'Saved local settings to: {settings_file}')
    return settings_file.as_posix()


def copy(from_project: pd.AProject, to_project: pd.AProject) -> str:
    """
    Copy settings from one project to another.
    """
    from_project_settings = load(from_project)
    return save(from_project_settings, to_project)
