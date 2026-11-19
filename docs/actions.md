## Вызов экшенов

### Через команду

Для вызова экшена через команду используейте такой синтаксис:

```shell
agio action [action.name] [args] 
```

Чтобы вызвать в отдельном воркспейсе просто укажите его id через аргумент -w
В таком случае будут видны все экшены этого воркспейса доступные в его пакетах.

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

workspace_id = 'UUID'
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
    'action': 'desk.show_message',
    'kwargs': {
        "text": "hello world",
        "title": "Info"
    }
}
requests.post('http://localhost:8877/action', json=payload).json()

```


Для выполнения запроса в контексте проекта следует передать ID проекта.
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
    "app_name": "web",
    "menu_name": "app-launcher",
    "project_id": "<UUID>"
  }
}
```

## Список экшенов

Для отображения списка экшенов в различных меню и тулбарах нужно запросить их через http запрос на локальный сервер.
В запросе следует указать имя меню, имя и версию приложения для которого запрашивается состав. Таже можно вместо имени указать группу приложения.

```python
import requests
payload = {
    'action': 'actions.get_actions',
    'kwargs': {
        "menu_name": "tray_menu",   # запрос экшенов для главного меню в трее
        "app_name": "desk",
        "app_version": None
    }
}
requests.post('http://localhost:8877/action', json=payload).json()
# {
#   'status': 'OK', 
#   'message': None, 
#   'data': {
#       'name': 'tray_menu', 
#       'label': None, 
#       'items': [
#           {'type': 'action', 'action': 'desk.open_settings', 'name': 'desk.open_settings', 'label': 'Local Settings', 'icon': None, 'order': 50, 'group': '', 'app_name': ['desk'], 'package_name': 'agio_desk', 'args': [], 'kwargs': {}}, 
#           {'type': 'action', 'action': 'core.logout', 'name': 'core.logout', 'label': 'Log Out', 'icon': None, 'order': 98, 'group': '', 'app_name': ['desk'], 'package_name': 'agio_core', 'args': [], 'kwargs': {}}, 
#           {'type': 'action', 'action': 'core.login', 'name': 'core.login', 'label': 'Log In', 'icon': None, 'order': 99, 'group': '', 'app_name': ['desk'], 'package_name': 'agio_core', 'args': [], 'kwargs': {}}, 
#           {'type': 'action', 'action': 'core.exit', 'name': 'core.exit', 'label': 'Exit', 'icon': None, 'order': 100, 'group': '', 'app_name': ['desk'], 'package_name': 'agio_core', 'args': [], 'kwargs': {}}
#       ], 
#       'type': 'group', 
#       'group': 'tray_menu'
#   }
# }

```

## Menu Name

Имя меню или тулбара должно отражать назначение, но не расположение и не окружение.

Примеры:

- `tray_menu`
- `pipeline_menu`
- `publish_toolbar`

Неправильные примеры:

- `desk_menu`
- `maya_publish_menu`

Иногда у софта может мыть своё уникальное имя меню или тулбара, тогда конкретика доспустима

- `maya_button_menu`

Примеры расположения меню и тулбаров:

- главное меню в agio Desk
- пайплайн меню в софте
- специальное меню под софт
- панель инструментов в софте
- меню и панель инструментов в касмтоных инструментах
- меню и тулбар на фронте
- меню конкретного инстурмента\плагина


# Процесс запуска приложения


- запускается команда или приходит по сети запрос. срабатывает роут action

- если указан ws, то он создается

- запуск экшена внутри обычного (не dcc) воркспейса
WS-DIR/ptyhon -m agio action app_pauncher.launch --app ...

- срабатывают все колбеки воркспейса !!!, если у них нет фильтра. пока что запускается приложение standalone

- срабатывает метод launch в AppLauncherService. он определяет переменные приложения

- если у приложения есть python интерпретатор, то создается venv для приложения используя интерпретатор приложения

- приложение стартует, и в качестве PYTHONPATH указывается venv окружения сделанно из интерпретатора приложения. 
