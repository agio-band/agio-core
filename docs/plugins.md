
## Создание нового типа плагина

1. Наследоваться от `APlugin`
2. Определить атрибут `plugin_type`, атрибут `name` должен остаться пустым
3. Указать атрибут `___is_base_plugin__ = True`
4. При необходимости сделать `@abstractmethod` для обязательного переопределения

```python
from agio.core.plugins.base_plugin import APlugin
from abc import abstractmethod

class MyPluginType(APlugin):
    plugin_type = 'my_type'
    __is_base_plugin__ = True

    # optional
    @abstractmethod 
    def get_some(self):
        pass
```


## Создание плагина

1. Наследоваться от нужного типа плагина
2. Определить уникальный name
3. Определить нужные для типа методы (обычно execute())
4. Добавить определение в `__agio__.yml`

```python
from agio_package.base_classes import MyPluginType

class MyPlugin(MyPluginType):
    name = 'myplugin'
    
    def execute(self):
        pass
```

```yml
...
plugins:
  - name: myplugin
    label: My Plufin
    implementations:
        - module: plugins/myplugin.py
```
