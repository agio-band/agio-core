from __future__ import annotations
from ..entities import project as project_domain
from ..events import emit
from .fields.base_field import BaseField
from .fields.generic_fields import StringField, IntField, BaseField, FloatField
from .fields.compaund_fields import ListField, SetField, TupleField, DictField
from .fields.extended_fields import (
    DateTimeField,
    FrameRangeField,
    VectorField,
    Vector4Field,
    Vector3Field,
    Vector2Field,
    RGBColorField
)
from agio.core.settings.fields.editor_fields import JSONField, MarkdownField
from agio.core.settings.fields.special_fields import PluginSelectField
from agio.core.settings.package_settings import APackageSettings
from agio.core.settings import local_settings_manager
from agio.core.utils.settings_hub import LocalSettingsHub, WorkspaceSettingsHub
from agio.core.entities.workspace import AWorkspace
from ..exceptions import SettingsRevisionNotExists


def get_local_settings(project: project_domain.AProject = None) -> LocalSettingsHub:
    # create local settings instance with applied values
    local_settings = local_settings_manager.load_local_settings()#project)
    emit('core.settings.local_settings_loaded', {'settings': local_settings})
    return local_settings


def save_local_settings(settings: LocalSettingsHub):#, project: project_domain.AProject = None) -> str:
    return local_settings_manager.save_local_settings(settings)#, project)


def get_workspace_settings(workspace: AWorkspace = None) -> WorkspaceSettingsHub:
    # create workspace instance
    ws = workspace or AWorkspace.current()
    # get workspace settings from server
    try:
        revision = ws.get_current_revision()
        settings_data = revision.get_settings_data()  # TODO
    except SettingsRevisionNotExists:
        settings_data = {}
        revision = None
    # create workspace settings instance with applied values
    settings = WorkspaceSettingsHub(settings_data)
    emit('core.settings.workspace_settings_loaded', {
        'settings': settings, 'workspace': ws, 'revision': revision})
    return settings
