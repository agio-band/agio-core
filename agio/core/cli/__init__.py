import click


class Env(click.ParamType):
    name = "env_var"

    def convert(self, value, param, ctx):
        if '=' not in value:
            self.fail(f"Invalid environment variable format: {value}.  Expected KEY=VALUE.", param, ctx)
        key, val = value.split('=', 1)
        return key, val

    def get_metavar(self, param):
        return 'KEY=VALUE'
