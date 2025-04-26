from typing import Literal

from pydantic import BaseModel


_SUPPORTED_CLOUD_PROVIDERS = ["azure", "gcp"]


# Database
class DatabaseConfig(BaseModel):
    host: Literal["local", "azure"]
    endpoint: str
    collection: str | dict[str, str]
    database: str | None = None
    api_key: str | None = None


class DatabaseTypeConfig(BaseModel):
    chat: DatabaseConfig | None = None
    vector: DatabaseConfig | None = None


# Models
class ModelConfig(BaseModel):
    api_key: str
    api_url: str
    api_version: str
    model: str


class ModelsConfig(BaseModel):
    llm: ModelConfig
    embeddings: ModelConfig


# Secrets
class SecretsSecretConfig(BaseModel):
    name: str
    value: str


class SecretsVaultConfig(BaseModel):
    name: str | None
    secrets: list[SecretsSecretConfig]


class SecretsHostConfig(BaseModel):
    name: Literal["local", *_SUPPORTED_CLOUD_PROVIDERS]  # type: ignore
    vaults: list[SecretsVaultConfig]


class SecretsConfig(BaseModel):
    hosts: list[SecretsHostConfig]


# Yaml
class YamlConfig(BaseModel):
    databases: DatabaseTypeConfig
    models: ModelsConfig
    secrets: SecretsConfig
