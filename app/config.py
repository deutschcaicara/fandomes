"""
Configurações centralizadas usando Pydantic.
Qualquer módulo deve importar a instância `settings`
em vez de ler variáveis de ambiente diretamente.
"""
import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, AnyHttpUrl,ConfigDict

class Settings(BaseSettings):
    # ➜ Aceita variáveis extras e carrega .env
    model_config = ConfigDict(
        extra='allow',               
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
    )
# ─── Novas linhas ───
    BASE_DIR: str = Field(
        default=str(Path(__file__).resolve().parent), env="BASE_DIR"
    )
    
   
    API_PORT: int = Field(8000, env="API_PORT")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    MONGO_URI: str = Field(..., env="MONGO_URI")

    WHATSAPP_API_URL: AnyHttpUrl = Field(..., env="WHATSAPP_API_URL")
    WHATSAPP_TOKEN: str = Field(..., env="WHATSAPP_TOKEN")

    OLLAMA_API_URL: AnyHttpUrl = Field(..., env="OLLAMA_API_URL")
    OLLAMA_MODEL: str = Field("gemma:3b", env="OLLAMA_MODEL")

    MCP_TIMEOUT_S: int = Field(10, env="MCP_TIMEOUT_S")

@lru_cache
def _cached_settings() -> Settings:
    return Settings()

settings: Settings = _cached_settings()

globals().update({k: getattr(settings, k) for k in dir(settings) if k.isupper()})

@lru_cache
def _cached_settings() -> Settings:
    return Settings()

settings: Settings = _cached_settings()

globals().update({k: v for k, v in settings.model_dump().items()})
# --------------