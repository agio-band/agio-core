
# base
class AException(Exception):
    detail: str = "Application Error"

    def __init__(self, detail: str = None):
        super().__init__(detail or self.detail)


# packages
class PackageError(AException):
    detail: str = "Package Error"


class PackageLoadingError(AException):
    detail: str = "Package Loading Error"


class PackageNotFound(AException):
    detail: str = "Package Not Found"

class PackageRuntimeError(AException):
    detail: str = "Package Runtime Error"


class PackageMetadataError(AException):
    detail: str = "Package Metadata Error"


class PackageRepositoryError(AException):
    detail: str = "Package Repository Error"


# api
class ApiError(AException):
    detail: str = "Workspace Error"


class NotExistsError(ApiError):
    detail: str = "Entity does not exist"


class WorkspaceNotExists(NotExistsError):
    detail: str = "Workspace does not exist"


class RevisionNotExists(NotExistsError):
    detail: str = "Workspace revision does not exist"


class SettingsRevisionNotExists(NotExistsError):
    detail: str = "Settings revision does not exist"


class WorkspaceNotInstalled(ApiError):
    detail: str = "Workspace Not Installed"


class MakeReleaseError(AException):
    detail: str = "Make Release Error"


class ProjectNotExists(NotExistsError):
    detail: str = "Project does not exist"


class EntityNotExists(NotExistsError):
    detail: str = "Entity does not exist"


class ProductNotExists(NotExistsError):
    detail: str = "Product does not exist"


# Event hub
class EventHubError(AException):
    detail = 'Event hub error'


class StopEventPropagate(EventHubError):
    detail = 'Stop event propagate'


class EventNameError(AException):
    detail = 'Event name error'


class EventCreationError(AException):
    detail = 'Event creation error'


class EventRuntimeError(EventHubError):
    detail = 'Event runtime error'


class CallbackInitError(EventHubError):
    detail = 'Callback init error'


# settings
class SettingsError(AException):
    detail = "Settings error"


class NotSupportedTypeError(SettingsError):
    detail = "Settings type not supported"


class SettingsInitError(SettingsError):
    detail = "Settings initialization error"


class RequiredValueNotSetError(SettingsInitError):
    detail = "Required value not set"


class ValueTypeError(SettingsError):
    detail = "Value type error"

class ParameterError(SettingsError):
    detail = "Parameter error"

# cli

# plugins
class PluginError(AException):
    detail = "Plugin error"


class PluginLoadingError(PluginError):
    detail = "Plugin loading error"


class PluginNotFoundError(PluginError):
    detail = "Plugin not found"


# api
class NotAuthorizedError(AException):
    detail = 'Not authorized. Use command "agio auth login" to authorize.'

class AuthorizationError(AException):
    detail = "Authorization error"


class RequestError(AException):
    detail = "Request error"

# services
class ServiceStartupError(AException):
    detail = "Service startup error"
