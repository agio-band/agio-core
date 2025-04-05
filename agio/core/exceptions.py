

class AppError(Exception):
    pass


class WorkspaceError(AppError):
    pass


class WorkspaceNotExists(WorkspaceError):
    pass


class WorkspaceNotInstalled(WorkspaceError):
    pass


class PackageError(AppError):
    pass
