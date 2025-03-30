

class AppError(Exception):
    pass


class WorkspaceError(AppError):
    pass


class WorkspaceNotExists(WorkspaceError):
    pass


class PackageError(AppError):
    pass
