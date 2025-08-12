from agio.core.cli import setup_commands


def run_command(*args: str):
    try:
        setup_commands.agio_group.main(args=list(args), standalone_mode=False)
    except SystemExit as e:
        return e.code


