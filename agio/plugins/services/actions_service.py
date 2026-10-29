import json
import logging

from agio.core.actions import get_actions, make_action
from agio.core.entities.project import AProject
from agio.core.exceptions import WorkspaceInstallationLocked
from agio.core.plugins.base_service import ServicePlugin
from agio.tools import launching

logger = logging.getLogger(__name__)

class ActionsService(ServicePlugin):
    name = 'actions'
    def execute(self, **kwargs):
        pass

    @make_action()
    def get_actions(
            self,
            menu_name: str,
            app_name: str,
            app_group: str = None,
            app_version: str = None,
            action_group: str = None,
            *args,
            **kwargs,
    ):
        project_id = kwargs.get('project_id')
        if not project_id:
            # from current workspace
            logger.debug('No project id provided, get core items')
            group_item = get_actions(
                menu_name,
                app_name,
                app_group=app_group,
                app_version=app_version,
                action_group=action_group,
            )
            response = group_item.serialize()
            return response
        else:
            # from different workspace
            project = AProject(project_id)
            workspace = project.get_workspace()
            if not workspace:
                raise Exception(f'No workspace found for project {project.name}')
            logger.debug(f'Get items for workspace {workspace}')
            if workspace.get_manager().install_lock.locked():
                raise WorkspaceInstallationLocked
            cmd = [
                'get-actions',
                '-m', menu_name,
                '-a',app_name
            ]
            if app_group:
                cmd += ['--app-group', app_group]
            if app_version:
                cmd += ['--app-version', app_version]
            if action_group:
                cmd += ['--action-group', action_group]
            logger.debug('COMMAND: ' + ' '.join(cmd))
            output = launching.exec_agio_command(cmd, workspace=workspace.id, use_custom_pipe=True)
            if output.strip():
                try:
                    logger.debug(f'Actions output: {output}')
                    return json.loads(output)
                except json.decoder.JSONDecodeError:
                    raise Exception(f'Failed to decode actions output from {output}')
            else:
                return {'error': 'No output'}



