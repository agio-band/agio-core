

class PackageManagerBase:
    def install_package(self, package_name):
        raise NotImplementedError

    def uninstall_package(self, package_name):
        raise NotImplementedError

    def list_installed_packages(self):
        raise NotImplementedError

    def update_package(self, package_name):
        raise NotImplementedError

    def search_package(self, package_name):
        raise NotImplementedError

    def get_package_info(self, package_name):
        raise NotImplementedError

    def get_package_version(self, package_name):
        raise NotImplementedError

    def create_venv(self, venv_name):
        raise NotImplementedError

    def delete_venv(self, venv_name):
        raise NotImplementedError

    def list_venvs(self):
        raise NotImplementedError
