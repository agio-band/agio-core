
class BasePluginClass:
    is_base_class = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__mro__[1] is not BasePluginClass:
            cls.is_base_class = False