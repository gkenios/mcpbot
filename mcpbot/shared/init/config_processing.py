from typing import TypedDict

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from mcpbot.shared.config import CONFIG_FILE, DatabaseConfig, YamlConfig
from mcpbot.shared.services import (
    ChatDB,
    SecretFactory,
    VectorDB,
    get_chat_db,
    get_embeddings,
    get_llm,
    get_vector_db,
)
from mcpbot.shared.utils import ArbitaryTypesModel, Singleton, read_file


class AppDatabases(ArbitaryTypesModel):
    chat: dict[str, ChatDB]
    vector: dict[str, VectorDB]


class AppModels(ArbitaryTypesModel):
    embeddings: Embeddings
    llm: BaseChatModel


class AppConfig(ArbitaryTypesModel):
    databases: AppDatabases
    models: AppModels
    secrets: dict[str, str]


class ConfigSingleton(metaclass=Singleton):
    """Class to store the configuration."""

    def __init__(self) -> None:
        self.config = YamlConfig(**read_file(CONFIG_FILE))
        # Process the secrets first
        self.secrets = self.get_secrets()
        # Then define the transformer models as vector databases need embeddings
        self.models = self.get_models()
        # Finally, define the databases
        self.databases = self.get_databases()

        self.app_config = AppConfig(
            databases=self.databases,
            models=self.models,
            secrets=self.secrets,
        )

    def get_models(self) -> AppModels:
        return AppModels(
            embeddings=get_embeddings(**self.config.models.embeddings.__dict__),
            llm=get_llm(**self.config.models.llm.__dict__),
        )

    def get_databases(self) -> AppDatabases:
        class DBTypes(TypedDict):
            chat: dict[str, ChatDB]
            vector: dict[str, VectorDB]

        db = self.config.databases
        app_databases_kwargs: DBTypes = {"chat": dict(), "vector": dict()}
        database_pickers = [get_chat_db, get_vector_db]

        for key, picker in zip(app_databases_kwargs.keys(), database_pickers):
            db_config: DatabaseConfig = getattr(db, key)
            collection: dict[str, DBTypes] = dict()

            for collect_key, collect_value in db_config.collections.items():
                # Define the kwargs for the DBFactory object
                kwargs = {
                    key: value
                    for key, value in db_config.__dict__.items()
                    if key != "collections"
                }
                kwargs["collection"] = collect_value
                if key == "vector":
                    kwargs["embeddings"] = self.models.embeddings

                collection[collect_key] = picker(**kwargs)  # type: ignore [operator]
            app_databases_kwargs[key] = collection  # type: ignore [literal-required]
        return AppDatabases(**app_databases_kwargs)

    def get_secrets(self) -> dict[str, str]:
        secrets = dict()
        for host in self.config.secrets.hosts:
            # Iterate over vaults
            for vault in host.vaults:
                secrets_mapping = dict()
                for secret in vault.secrets:
                    secrets_mapping[secret.name] = secret.value

                # Get the secrets
                retrieved_secrets = (
                    SecretFactory[host.name]
                    .value()
                    .get(secrets_mapping.values(), vault.name)
                )
                secrets.update(
                    {
                        key: retrieved_secrets[value]
                        for key, value in secrets_mapping.items()
                    }
                )
        # Re-red the config and parse the secrets
        self.config = YamlConfig(**read_file(CONFIG_FILE, secrets))
        return secrets


config = ConfigSingleton().app_config
