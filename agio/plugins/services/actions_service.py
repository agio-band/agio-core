import json

from agio.core.entities.project import AProject
from agio.core.plugins.base_service import ServicePlugin, make_action
from agio.core.utils import get_actions
from agio.core.utils.launch_utils import exec_agio_command


class ActionsService(ServicePlugin):
    name = 'actions'
    def execute(self, **kwargs):
        pass

    @make_action()
    def get_actions(self, menu_name: str, app_name: str, *args, **kwargs):
        project_id = kwargs.get('project_id')
        if not project_id:
            # from current workspace
            action_group = get_actions(menu_name, app_name)
            response = action_group.serialize()
            return response
        else:
            # from different workspace
            project = AProject(project_id)
            workspace = project.get_workspace()
            if not workspace:
                raise Exception(f'No workspace found for project {project.name}')
            cmd = [
                'get-actions',
                '-m', menu_name,
                '-a',app_name
            ]
            output = exec_agio_command(cmd, workspace=workspace.id, use_custom_pipe=True)
            if output.strip():
                try:
                    return json.loads(output)
                except json.decoder.JSONDecodeError:
                    raise Exception(f'Failed to decode actions output from {output}')
            else:
                return {'error': 'No output'}



