from abc import ABC, abstractmethod

from langchain_core.embeddings.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from pydantic import BaseModel, SecretStr


class LLM(BaseModel, ABC):
    model: str
    api_key: SecretStr
    api_url: str | None = None
    api_version: str | None = None

    @abstractmethod
    def auth(self) -> BaseChatModel:
        raise NotImplementedError


class AzureLLM(LLM):
    def auth(self) -> BaseChatModel:
        return AzureChatOpenAI(
            azure_endpoint=self.api_url,
            azure_deployment=self.model,
            api_key=self.api_key,
            api_version=self.api_version,
        )


def get_llm(
    model: str,
    api_key: SecretStr,
    api_url: str | None = None,
    api_version: str | None = None,
) -> BaseChatModel:
    if isinstance(api_url, str) and api_url.strip("/").endswith("azure.com"):
        llm_object = AzureLLM
    # This is a placeholder for future LLM
    else:
        pass
    return llm_object(
        model=model,
        api_key=api_key,
        api_url=api_url,
        api_version=api_version,
    ).auth()


class BaseEmbeddings(BaseModel, ABC):
    model: str
    api_key: SecretStr
    api_url: str | None = None
    api_version: str | None = None

    @abstractmethod
    def auth(self) -> Embeddings:
        raise NotImplementedError


class AzureEmbeddings(BaseEmbeddings):
    def auth(self) -> Embeddings:
        return AzureOpenAIEmbeddings(
            azure_endpoint=self.api_url,
            azure_deployment=self.model,
            api_key=self.api_key,
            api_version=self.api_version,
        )


def get_embeddings(
    model: str,
    api_key: SecretStr,
    api_url: str | None = None,
    api_version: str | None = None,
) -> Embeddings:
    if isinstance(api_url, str) and api_url.strip("/").endswith("azure.com"):
        llm_object = AzureEmbeddings
    # This is a placeholder for future Embeddings
    else:
        pass
    return llm_object(
        model=model,
        api_key=api_key,
        api_url=api_url,
        api_version=api_version,
    ).auth()
