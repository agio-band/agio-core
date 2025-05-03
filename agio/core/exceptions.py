class AError(Exception):
    pass


class WorkspaceError(AError):
    pass


class WorkspaceNotExists(WorkspaceError):
    pass


class WorkspaceNotInstalled(WorkspaceError):
    pass


class PackageError(AError):
    pass


