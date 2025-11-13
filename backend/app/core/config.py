"""
Configuration management for Software Maker Agent Platform.
Loads settings from YAML and environment variables.
"""
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LLMProviderConfig(BaseModel):
    """Configuration for a single LLM provider."""
    enabled: bool = False
    api_key_env: Optional[str] = None
    model: str
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7


class LLMConfig(BaseModel):
    """LLM routing configuration."""
    mode: str = "hybrid"  # "openai", "claude", "local", "hybrid"
    providers: Dict[str, LLMProviderConfig] = Field(default_factory=dict)
    routing: Dict[str, List[str]] = Field(default_factory=dict)
    fallback_enabled: bool = True
    max_retries: int = 3


class AppConfig(BaseModel):
    """Application-level configuration."""
    base_url: str = "http://localhost:8000"
    projects_dir: str = "/app/projects"
    max_retries: int = 5
    max_concurrent_projects: int = 10
    max_fix_attempts: int = 5
    worker_concurrency: int = 4


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = "postgresql+asyncpg://smaker:smaker@db:5432/smaker"
    pool_size: int = 20
    max_overflow: int = 10
    echo: bool = False


class RedisConfig(BaseModel):
    """Redis configuration."""
    url: str = "redis://redis:6379/0"
    max_connections: int = 50


class GitConfig(BaseModel):
    """Git integration configuration."""
    github_enabled: bool = True
    gitlab_enabled: bool = True
    github_token_env: str = "GITHUB_TOKEN"
    gitlab_token_env: str = "GITLAB_TOKEN"
    auto_commit: bool = True
    auto_push: bool = False


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    log_to_file: bool = True
    log_dir: str = "/app/logs"


class Config(BaseModel):
    """Main configuration."""
    app: AppConfig = Field(default_factory=AppConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


class Settings(BaseSettings):
    """Environment-based settings."""
    config_path: str = "./configs/config.yaml"

    # API Keys from environment
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None

    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file."""
    settings = Settings()

    if config_path is None:
        config_path = settings.config_path

    config_file = Path(config_path)

    if not config_file.exists():
        print(f"Warning: Config file {config_path} not found. Using defaults.")
        return Config()

    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)

    return Config(**config_data)


# Global config instance
_config: Optional[Config] = None
_settings: Optional[Settings] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_config():
    """Reload configuration from file."""
    global _config
    _config = load_config()
