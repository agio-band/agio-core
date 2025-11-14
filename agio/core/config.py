from pydantic_settings import BaseSettings as BaseConfig, SettingsConfigDict

from agio.tools import app_dirs

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
    PLATFORM_URL: str = "https://platform.agio.services"        # <= production url
    # api client id
    CLIENT_ID: str = "b5431a17-4c52-43cf-b71b-ac700b43985f"     # <= default for prod
    # auth local server port
    AUTH_LOCAL_PORT: int = 9082
    # git repository connectio attempts
    MAX_REQUEST_ATTEMPTS: int = 5
    MAX_LOGIN_ATTEMPTS: int = 2


class WorkspaceSettings(_BaseSettings):
    # additional resources dir
    RESOURCES_DIR: str = ""
    CACHE_ROOT: str = app_dirs.cache_dir().as_posix()
    INSTALL_DIR: str = app_dirs.workspaces_install_dir().as_posix()


class PackagesConfig(_BaseSettings):
    STORE_URL: str = "https://store.agio.services"  # TODO


class CLIConfig(_BaseSettings):
    DISABLE_CUSTOM_PIPE_RESULT: bool = False


class CoreConfig(BaseConfig):
    API: ApiSettings = ApiSettings()
    WS: WorkspaceSettings = WorkspaceSettings()
    PKG: PackagesConfig = PackagesConfig()
    CLI: CLIConfig = CLIConfig()


config = CoreConfig()