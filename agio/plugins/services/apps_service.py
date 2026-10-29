import logging
import os
import shlex

from agio.apps import get_app_list
from agio.apps.context_app import ContextApp
from agio.apps.launcher import AApplicationLauncher
from agio.core.actions import make_action
from agio.core.entities.task import ATask
from agio.core.events import emit
from agio.core.plugins.base_service import ServicePlugin
from agio.tools import launching, env_names

logger = logging.getLogger(__name__)


class AppLauncherService(ServicePlugin):
    name = 'app_launcher'

    @make_action(label='Launch App')
    def launch(self, *args, app: str, **kwargs):
        workspace_id = kwargs.get('workspace_id') or os.getenv(env_names.WORKSPACE_ID)
        task_id = kwargs.get('task_id')
        if not workspace_id and task_id:
            workspace_id = ATask(task_id).project.workspace_launching_id
        envs = kwargs.get('envs', {})
        cmd_args = ['launch', '--app', f'{app}']
        if args:
            cmd_args.append('--')
            cmd_args.extend([shlex.quote(a) for a in args])
        context = {
            'cmd': cmd_args,
            'workspace_id': workspace_id,
            'envs': envs,
            'task_id': task_id,
        }
        emit('core.apps.before_launch_service', {'context': context, 'kwargs': kwargs})
        cmd_args = context['cmd']
        workspace_id = context['workspace_id']
        envs = context['envs']
        app_context = ContextApp(app)
        envs.update({
            env_names.APP_VARIANT: app_context.variant
        })
        if os.getenv(env_names.DEBUG):
            envs[env_names.DEBUG] = 'true'
        if not workspace_id:
            raise ValueError(f'Workspace ID not provided')
        if task_id:
            envs[env_names.TASK_ID] = task_id
        detached = kwargs.get('detached', True)
        logger.debug(f'Launching app {app} in workspace {workspace_id}')
        logger.debug(f'Cmd Args: {" ".join(cmd_args)}')
        launching.exec_agio_command(
            args=cmd_args,
            workspace=workspace_id,
            envs=envs,
            detached=detached,
            new_console=detached,
            # TODO get from kwargs
            # keep_console=True
        )
        return True

    def collect_actions(self, hidden=False, **kwargs) -> list:
        # TODO: filter for project using settings
        apps: list[AApplicationLauncher] = get_app_list()
        items = []
        action_name = f'{self.name}.{self.launch.__name__}'
        for i, app in enumerate(sorted(apps, key=lambda a: (a.name, a.version))):
            label = f'{app.label} {app.version or ""}'.strip()
            if app.mode:
                label += f' ({app.mode})'
            action_data = {
                # filters
                'action': action_name,
                'menu_name': 'launcher_menu',
                'app_name': {'web', 'desk'},
                # action properties
                'name': 'launch',
                'label': label,
                'icon': app.icon,
                'hidden': app.plugin.hidden,
                'order': i,
                'group': 'Applications',
                'kwargs': {
                    'app': app.app_argument,
                },
                'args': (),
            }
            if not self._match_action_filters(action_data, hidden=hidden, **kwargs):
                continue
            items.append(action_data)
        return items
