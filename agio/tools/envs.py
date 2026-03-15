import os
import site

import click


def get_agio_envs(py_envs: bool =False, to_output: bool = False) -> dict|None:
    keys = [k for k in os.environ.keys() if k.startswith('AGIO_')]
    extra_values = {}
    if py_envs:
        keys.extend([k for k in os.environ.keys() if k.startswith('PYTHON_')])
        keys.append('PATH')
        site_paths = ':'.join([site.getusersitepackages()] + site.getsitepackages())
        keys.append('SITE-PACKAGES')
        extra_values['SITE-PACKAGES'] = site_paths

    if to_output:
        if not keys:
            print('No AGIO env found')
            return
        max_length = max(len(k) for k in keys)
        for k in sorted(keys):
            value = os.environ.get(k) or extra_values.get(k)
            if is_multipath_env(value):
                parts = value.split(':')
                click.secho(f"{k:>{max_length + 2}} = {parts[0]}", fg='green')
                for part in parts[1:]:
                    click.secho(f"{' ':>{max_length + 5}}{part}", fg='green')
            else:
                click.secho(f"{k:>{max_length + 2}} = {value}", fg='green')
    else:
        return {key: os.getenv(key) for key in keys}


def is_multipath_env(value: str) -> bool:
    if os.pathsep not in value:
        return False
    else:
        if value.startswith('http'):
            return False
        return True
