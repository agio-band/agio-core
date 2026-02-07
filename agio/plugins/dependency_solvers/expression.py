import os
from functools import partial
from typing import Any

from agio.core.plugins.base_dependency_plugin import SettingsDependencySolverPlugin
from agio.tools.expression_solver import ExpressionSolver


class ExpressionDependencySolverPlugin(SettingsDependencySolverPlugin):
    """
    Expression Dependency (WIP)
    """
    name = 'exp'

    def execute(self, field, package_settings, settings_hub, **kwargs):
        dep = field.get_dependency()
        solver = ExpressionSolver(partial(self.get_value, settings_hub, kwargs))
        return solver.solve(dep.value)

    def get_value(self, settings_hub, kwargs: dict, name: str) -> Any:
        if '.' in name:
            return settings_hub.get(name)
        elif name.isupper():
            return os.getenv(name)
        context = kwargs.get('context')
        if context and name in context:
            return context[name]
        raise NameError(f'Variable named {name} not found')
