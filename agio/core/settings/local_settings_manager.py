from __future__ import annotations
import json
import logging
import os
from pathlib import Path

from agio.core.domains import project as project_domain
from agio.core.utils import app_dirs
from agio.core.utils.json_serializer import JsonSerializer
from agio.core.utils import settings_hub

logger = logging.getLogger(__name__)

_settings_dir = Path(os.getenv('AGIO_SETTINGS_DIR') or app_dirs.settings_dir())
_settings_file_name = 'settings.json'


def get_settings_dir(project_id: str = None):
    project_id = project_id or os.getenv('AGIO_PROJECT_ID')
    if not project_id:
        raise ValueError('Project ID is required')
    settings_dir = _settings_dir.joinpath(project_id)
    return settings_dir


def load_local_settings(project: str|project_domain.AProject = None) -> settings_hub.LocalSettingsHub:
    settings_data = {}
    if isinstance(project, project_domain.AProject):
        project = project.id
    settings_file = Path(get_settings_dir(project or 'default'), _settings_file_name)
    if settings_file.exists():
        settings_data.update(json.loads(settings_file.read_text(encoding='utf-8')))
    settings = settings_hub.LocalSettingsHub(settings_data)
    logger.debug(f'Loaded settings from {settings_file}')
    return settings


def save_local_settings(settings: settings_hub.LocalSettingsHub, project: str|project_domain.AProject=None) -> str:
    project = project or 'default'
    if isinstance(project, project_domain.AProject):
        project = project.id
    settings_file = Path(get_settings_dir(project), _settings_file_name)
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    settings_file.write_text(json.dumps(settings.dump(), indent=2, cls=JsonSerializer))
    logger.debug(f'Saved local settings to: {settings_file}')
    return settings_file.as_posix()
