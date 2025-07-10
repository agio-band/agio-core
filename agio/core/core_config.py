from pathlib import Path
from pydantic_settings import BaseSettings as BaseConfig, SettingsConfigDict


env_file_path = Path(".env")


class _BaseSettings(BaseConfig):
    model_config = SettingsConfigDict(
        env_file=(env_file_path.as_posix()),
        case_sensitive=True,
        extra="ignore",
    )


class ApiSettings(_BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGIO_API_", extra="ignore")
    # all api methods must return pydantic schemas instead dicts
    USE_RESPONSE_SCHEMA: bool = True
    # request timeout
    REQUEST_TIMEOUT: int = 5
    # base url
    PLATFORM_URL: str = "https://platform.agio.services"
    # default api client
    DEFAULT_CLIENT_ID: str = "b5431a17-4c52-43cf-b71b-ac700b43985f"
    # auth local server port
    AUTH_LOCAL_PORT: int = 9082


class WorkspaceSettings(_BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGIO_", extra="ignore")

    RESOURCES_DIR: str = ""
    WORKSPACES_ROOT: str = "~/.agio/workspaces"


class CoreConfig(BaseConfig):
    api: ApiSettings = ApiSettings()
    workspace: WorkspaceSettings = WorkspaceSettings()


