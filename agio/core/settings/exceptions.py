from agio.core.exceptions import AError


class ASettingsError(AError):
    pass


class NotSupportedTypeError(ASettingsError):
    pass


class SettingsInitError(ASettingsError):
    pass


class RequiredValueNotSetError(SettingsInitError):
    pass

class ValueTypeError(ASettingsError):
    pass