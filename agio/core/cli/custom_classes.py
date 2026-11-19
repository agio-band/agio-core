import click
from click import Parameter, Context


class Env(click.ParamType):
    name = "env_var"

    def convert(self, value, param, ctx):
        if '=' not in value:
            self.fail(f"Invalid environment variable format: {value}.  Expected KEY=VALUE.", param, ctx)
        key, val = value.split('=', 1)
        return key, val

    def get_metavar(self, param: Parameter, ctx: Context):
        return 'KEY=VALUE'


class CustomGroup(click.Group):
    def resolve_command(self, ctx, args):
        try:
            cmd, cmd_name, args = super().resolve_command(ctx, args)
            if not hasattr(ctx, 'obj') or ctx.obj is None:
                ctx.obj = {}
            ctx.obj.update({
                'is_unknown_command': False,
                'cmd_name': cmd_name.name,
                'cmd_args': args,
                'resolved_command': cmd
            })
            return cmd, cmd_name, args

        except click.exceptions.UsageError as e:
            if args and "No such command" in str(e):
                cmd_name = args[0]
                if not hasattr(ctx, 'obj') or ctx.obj is None:
                    ctx.obj = {}
                ctx.obj.update({
                    'is_unknown_command': True,
                    'cmd_name': cmd_name,
                    'cmd_args': args[1:],
                    'resolved_command': None
                })
                @click.command(name=cmd_name)
                def stub_cmd():
                    pass
                return stub_cmd, cmd_name, args[1:]
            raise
