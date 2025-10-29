

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def instance(cls, raise_if_not_found=True):
        inst = cls._instances.get(cls)
        if inst is None and raise_if_not_found:
            raise RuntimeError(f'{cls.__name__} instance not initialized')
        return inst
