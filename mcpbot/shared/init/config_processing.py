from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from mcpbot.shared.config import CONFIG_FILE, YamlConfig
from mcpbot.shared.services import (
    ChatDB,
    ChatDBFactory,
    SecretFactory,
    VectorDB,
    VectorDBFactory,
    get_embeddings,
    get_llm,
)
from mcpbot.shared.utils import ArbitaryTypesModel, Singleton, read_file


class AppDatabases(ArbitaryTypesModel):
    chat: ChatDB | dict[str, ChatDB] | None = None
    vector: VectorDB | None = None


class AppModels(ArbitaryTypesModel):
    embeddings: Embeddings | None = None
    llm: BaseChatModel | None = None


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
        db = self.config.databases
        if db.vector:
            kwargs = {
                key: value
                for key, value in db.vector.__dict__.items()
                if key != "host"
            }
            vector_db = VectorDBFactory[db.vector.host].value(
                embeddings=self.models.embeddings,
                **kwargs,
            )
        else:
            vector_db = None

        if db.chat:
            if isinstance(db.chat.collection, str):
                kwargs = {
                    key: value
                    for key, value in db.chat.__dict__.items()
                    if key != "host"
                }
                chat_db = ChatDBFactory[db.chat.host].value(**kwargs)
            elif isinstance(db.chat.collection, dict):
                collections = dict()
                for collect_key, collect_value in db.chat.collection.items():
                    kwargs = {
                        key: value
                        for key, value in db.chat.__dict__.items()
                        if key != "host"
                    }
                    kwargs["collection"] = collect_value
                    chat_db = ChatDBFactory[db.chat.host].value(**kwargs)
                    collections[collect_key] = chat_db
                chat_db = collections
            else:
                raise ValueError("Collection must be a string or a dictionary.")
        else:
            chat_db = None
        return AppDatabases(chat=chat_db, vector=vector_db)

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
