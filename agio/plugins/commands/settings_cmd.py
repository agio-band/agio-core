import json
import textwrap

import click

from agio.core.plugins.base_command import ACommandPlugin


class SettingsCommand(ACommandPlugin):
    name = 'settings_cmd'
    command_name = 'settings'
    arguments = [
        click.option('-s', '--skip-defaults', help='Skip Default Values', is_flag=True),
        click.option('-p', '--project_id', required=False, help='Project ID'),
        click.argument('packages', nargs=-1, required=False),
    ]
    help = 'Settings info'

    def execute(self, skip_defaults, project_id, packages):
        from agio.core.settings import local_settings

        self._print_settings_from_hub(
            local_settings.get_settings_dir(project_id),
            local_settings.load(project_id),
            'LOCAL SETTINGS',
            project_id,
            skip_defaults,
            packages,
        )

    def _print_settings_from_hub(self, settings_dir, hub, title: str, project_id=None, skip_defaults=False, packages=None):
        line = lambda: print("=" * 50)

        line()
        click.secho(title, fg="yellow")
        print('Location:', settings_dir)
        if project_id:
            print('Project ID:', project_id)
        line()
        max_len = 0
        for name, pkg in hub.iter_package_settings():
            if packages and name not in packages:
                continue
            for field_name, field in pkg.iter_fields():
                max_len = max(max_len, len(field_name))
        printed_count = 0
        for name, pkg in hub.iter_package_settings():
            if packages and name not in packages:
                continue
            settings = pkg.__dump_settings__(skip_default=skip_defaults)
            if not settings:
                continue
            click.secho(f"{pkg.name}:", fg="green", bold=True)
            for field_name, field in settings.items():
                str_value = json.dumps(field['value'], indent=2)
                print_value = textwrap.indent(str_value, ' '*(max_len+4))[(max_len+4):]
                print(f"  {field_name:>{max_len}} = {print_value}")
            print('-' * 50)
            printed_count += 1
        if not printed_count:
            click.secho("Nothing to print!", fg="red")
        line()
