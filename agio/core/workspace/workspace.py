from uuid import UUID


class AWorkspace:
    def __init__(self, workspace_id: UUID):
        self.id = workspace_id
        self._data = {}
        self._installation_root = '' # from config

    def __str__(self):
        return self.name or self.id

    def __repr__(self):
        return f'<Workspace "{str(self)}">'

    @property
    def name(self):
        return

    @classmethod
    def create(cls, name: str):
        pass

    def install(self):
        pass

    def is_installed(self):
        pass

    def is_up_to_date(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass

    def get_root(self):
        pass

    def get_package_list(self):
        pass

    def get_package(self, name):
        pass

    def get_launch_envs(self):
        pass

    def get_pyexecutable(self):
        pass

    def collect_info(self):
        """
        File sizes
        Creation date
        Package count
            python libs
            agio packages
        """
        pass