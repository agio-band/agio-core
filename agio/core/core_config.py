from pydantic_settings import BaseSettings as BaseConfig, SettingsConfigDict

from agio.core.utils import app_dirs

env_file_path = app_dirs.config_dir() / 'core_config.env'


class _BaseSettings(BaseConfig):
    model_config = SettingsConfigDict(
        env_file=(env_file_path.as_posix()),
        case_sensitive=True,
        extra="ignore",
        env_prefix="AGIO_"
    )


class ApiSettings(_BaseSettings):
    # all api methods must return pydantic schemas instead dicts
    USE_RESPONSE_SCHEMA: bool = True
    # request timeout
    API_REQUEST_TIMEOUT: int = 5
    # base url
    PLATFORM_URL: str = "https://platform.agio.services"
    # default api client
    DEFAULT_CLIENT_ID: str = "b5431a17-4c52-43cf-b71b-ac700b43985f"
    # auth local server port
    AUTH_LOCAL_PORT: int = 9082


class WorkspaceSettings(_BaseSettings):
    RESOURCES_DIR: str = ""
    CACHE_ROOT: str = app_dirs.cache_dir().as_posix()
    INSTALL_DIR: str = app_dirs.default_workspace_install_dir().as_posix()


class PackagesConfig(_BaseSettings):
    STORE_URL: str = "https://store.agio.services"  # TODO


class CoreConfig(BaseConfig):
    API: ApiSettings = ApiSettings()
    WS: WorkspaceSettings = WorkspaceSettings()
    PKG: PackagesConfig = PackagesConfig()


