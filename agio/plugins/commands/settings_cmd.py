from agio.core.plugins.base_command import ACommandPlugin


class SettingsCommand(ACommandPlugin):
    name = 'settings_cmd'
    command_name = 'settings'
    arguments = [
        # click.option('-k', '--key', help='Show value of key'),
    ]
    help = 'Settings info'

    def execute(self):
        from agio import local_settings, workspace_settings

        self._print_settings_from_hub(local_settings, 'LOCAL SETTINGS')
        self._print_settings_from_hub(workspace_settings, 'WORKSPACE SETTINGS')

    def _print_settings_from_hub(self, hub, title: str):
        line = lambda: print("=" * 50)

        line()
        print(title)
        line()
        max_len = 0
        for name, pkg in hub.iter_package_settings():
            for field_name, field in pkg.iter_fields():
                max_len = max(max_len, len(field_name))
        for name, pkg in hub.iter_package_settings():
            print(f"{pkg.name}:")
            print('-' * 50)
            for field_name, field in pkg.iter_fields():
                print(f"  {field_name:>{max_len}} = {repr(field.get())}")
        line()