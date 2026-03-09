from agio.core.exceptions import AException


class ApplicationError(AException):
    pass


class ApplicationNotFoundError(AException):
    pass