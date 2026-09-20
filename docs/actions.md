# Вызов экшенов

### Через команду

Для вызова экшена через команду используейте такой синтаксис:

```shell
agio action [action.name] [args] 
```

Чтобы вызвать в отдельном воркспейсе просто укажите его id через аргумент -w
В таком случае будут видны все экшены этого воркспейса.

```shell
agio -w [UUID] action [action.name] [args]
```

### Из Python

```python

from agio.core.actions import execute_action

result = execute_action('action.name', 1, 2, key='value')
```
> Этот вызов следует исполнять в окружении нужного воркспейса 

Если команда должна возвращать результат в виде JSON, то удобно использовать отдельный пайп.

```python
from agio.tools.launching import exec_agio_command

workspace_id = ''
cmd = [
    'actions',
    '--key', 'value',
]
output = exec_agio_command(cmd, workspace=workspace_id, use_custom_pipe=True)
```


### Через web запрос на localhost

Отправить POST запрос на `http://localhost:8877/action` (порт может быть другой)

Данные запроса:
```json
{
  "action": "action.name",
  "kwargs": {
    "key1": "value",
    "key2": "value",
    "key3": "value"
  }
}
```

Пример

```py
import requests

payload = {
    'action': 'broker.ping',
    'kwargs': {}
}
requests.post('http://localhost:8877/action', json=payload).json()
# {'status': 'ok', 'message': None, 'data': {'result': 'pong'}}

payload = {
    'action': 'actions.get_actions',
    'kwargs': {
        "menu_name": "tray.main_menu",
        "app_name": "desk"
    }
}
requests.post('http://localhost:8877/action', json=payload).json()
# {
#   'status': 'OK', 
#   'message': None, 
#   'data': {
#       'name': 'tray.main_menu', 'label': None, 'items': [
#           {'type': 'action', 'action': 'desk.open_settings', 'name': 'desk.open_settings', 'label': 'Local Settings', 'icon': None, 'order': 50, 'group': '', 'app_name': ['desk'], 'package_name': 'agio_desk', 'args': [], 'kwargs': {}}, 
#           {'type': 'action', 'action': 'core.logout', 'name': 'core.logout', 'label': 'Log Out', 'icon': None, 'order': 98, 'group': '', 'app_name': ['desk'], 'package_name': 'agio_core', 'args': [], 'kwargs': {}}, 
#           {'type': 'action', 'action': 'core.login', 'name': 'core.login', 'label': 'Log In', 'icon': None, 'order': 99, 'group': '', 'app_name': ['desk'], 'package_name': 'agio_core', 'args': [], 'kwargs': {}}, 
#           {'type': 'action', 'action': 'core.exit', 'name': 'core.exit', 'label': 'Exit', 'icon': None, 'order': 100, 'group': '', 'app_name': ['desk'], 'package_name': 'agio_core', 'args': [], 'kwargs': {}}
#       ], 
#       'type': 'group', 
#       'group': 'tray.main_menu'
#   }
# }
```


Для выполннения запроса в контексте проекта следует передать ID проекта.
Например, чтобы запустить DCC в контексте конкретного проекта следует отправить такой запрос:

```json
{
  "action": "launcher.launch",
  "kwargs": {
    "app_name": "houdini",
    "app_version": "21.0.440",
    "task_id": "<UUID>"
  },
  "project_id": "<UUID>"
}
```
В этом случае экшен запустится в воркспейсе указанного проекта, а не в дефолтном.


Некоторые экшены запускаются в главном окружении, но внутри сами разбираются с конкретными проектами.
Для них требуется ID проекта отправить в `kwargs`. Тогда другой воркспейс не будет запускаться.

```json
{
  "action": "actions.get_actions",
  "kwargs": {
    "app_name": "front",
    "menu_name": "task.launcher",
    "project_id": "<UUID>"
  }
}
```

