from agio.core.cli.setup_commands import agio_group


def run_command(*args: str):
    try:
        agio_group.main(args=list(args), standalone_mode=False)
    except SystemExit as e:
        return e.code
