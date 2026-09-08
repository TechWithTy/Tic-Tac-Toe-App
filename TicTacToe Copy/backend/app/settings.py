from typing import Literal

from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5-mini"
    light_speed_mcp_url: AnyHttpUrl = "http://127.0.0.1:8500/mcp"
    light_speed_mcp_transport: Literal["streamable_http"] = "streamable_http"
    light_speed_mcp_timeout_seconds: float = 10.0
