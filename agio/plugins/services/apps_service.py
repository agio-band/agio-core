import logging

from agio.core.plugins.base_service import ServicePlugin, make_action
from agio.tools import launching, env_names
from agio_apps.utils import get_app_list, AApplicationLauncher
from agio_pipe.entities.task import ATask

logger = logging.getLogger(__name__)


class AppLauncherService(ServicePlugin):
    name = 'app_launcher'

    @make_action()
    def launch(self, *args, task_id: str, app_name: str, app_version: str, app_mode: str = None, **kwargs):
        task = ATask(task_id)
        workspace_id = kwargs.get('workspace_id') or task.project.workspace_launching_id
        if not workspace_id:
            raise ValueError(f'Workspace not set for project {task.project.name}')
        envs = {}
        cmd_args = [
            'launch',
            '--app-name', app_name,
            '--app-version', app_version,
        ]
        if app_mode:
            cmd_args.extend(['--app-mode', app_mode])
        if args:
            cmd_args.append('--')
            cmd_args.extend(args)
        if task_id:
            envs[env_names.TASK_ID] = task_id
        launching.exec_agio_command(
            args=cmd_args,
            workspace=workspace_id,
            envs=envs,
            detached=True,
            new_console=True,
        )

    def collect_actions(self, hidden=False):
        # TODO: filter for project using settings
        apps: list[AApplicationLauncher]  = get_app_list()
        items = []
        action_name = f'{self.name}.{self.launch.__name__}'
        for i, app in enumerate(sorted(apps, key=lambda a: (a.name, a.version))):
            label = f'{app.label} {app.version}'
            if app.mode_label:
                label += f' ({app.mode_label})'
            action_data = {
                # filters
                'action': action_name,
                'menu_name': 'task.launcher',
                'app_name': 'front',
                # action properties
                'name': 'launch',
                'label': label,
                'icon': app.icon,
                'order': i,
                'group': 'Applications',
                'kwargs': {
                    'app_name': app.name,
                    'app_version': app.version,
                    'app_mode': app.mode,
                },
                'args': (),
            }
            items.append(action_data)
        return items
