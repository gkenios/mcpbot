from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from langchain_core.embeddings.embeddings import Embeddings


class VectorDB(ABC):
    @abstractmethod
    def search(self, question: str, method: str, n_docs: int) -> list[str]:
        pass

    @abstractmethod
    def upsert(
        self,
        id: str,
        text: str,
        metadata: dict[str, Any],
    ) -> None:
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        pass

    @abstractmethod
    def get_by_id(self, id: str) -> dict[str, Any]:
        pass


class ChromaVectorDB(VectorDB):
    def __init__(
        self,
        embeddings: Embeddings,
        collection: str,
        endpoint: str,
        **kwargs: Any,
    ) -> None:
        from langchain_chroma import Chroma

        self.vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory=endpoint,
            collection_name=collection,
        )

    def search(self, question: str, method: str, n_docs: int) -> list[str]:
        method_map = {
            "cosine": "similarity",
            "euclidean": "similarity",
        }
        mapped_method = method_map[method]
        return [
            doc.page_content
            for doc in self.vector_store.search(
                query=question,
                search_type=mapped_method,
                k=n_docs,
            )
        ]

    def upsert(
        self,
        id: str,
        text: str,
        metadata: dict[str, Any],
    ) -> None:
        self.vector_store.add_texts(
            ids=[id],
            texts=[text],
            metadatas=[metadata],
        )

    def delete(self, id: str) -> None:
        self.vector_store.delete(ids=[id])

    def get_by_id(self, id: str) -> dict[str, Any]:
        result = self.vector_store.get_by_ids([id])[0]
        return {
            "id": result.id,
            "text": result.page_content,
            "metadata": result.metadata,
        }


class AzureCosmosVectorDB(VectorDB):
    def __init__(
        self,
        embeddings: Embeddings,
        database: str,
        collection: str,
        endpoint: str,
        api_key: str,
    ) -> None:
        from azure.cosmos import CosmosClient

        self.vector_store = (
            CosmosClient(endpoint, api_key)
            .get_database_client(database)
            .get_container_client(collection)
        )
        self.embeddings = embeddings

    def search(self, question: str, method: str, n_docs: int) -> list[str]:
        query_vector = self.embeddings.embed_query(question)
        query = (
            "SELECT TOP {n_docs} c.text "
            "FROM c "
            "ORDER BY VectorDistance(c.embedding, {query_vector}, true, {{'dataType': 'float32', 'distanceFunction': '{method}'}})"
        ).format(n_docs=n_docs, method=method, query_vector=query_vector)
        response = self.vector_store.query_items(
            query=query,
            enable_cross_partition_query=True,
        )
        return [item["text"] for item in response]

    def upsert(
        self,
        id: str,
        text: str,
        metadata: dict[str, Any],
    ) -> None:
        data = {
            "id": id,
            "text": text,
            "embedding": self.embeddings.embed_documents([text])[0],
            "metadata": metadata,
        }
        self.vector_store.upsert_item(data)

    def delete(self, id: str) -> None:
        self.vector_store.query_items(
            query=f"SELECT c.id FROM c WHERE c.id = '{id}'",
            enable_cross_partition_query=True,
        )
        self.vector_store.delete_item(id, partition_key=id)

    def get_by_id(self, id: str) -> dict[str, Any]:
        response = self.vector_store.query_items(
            query=f"SELECT * FROM c WHERE c.id = '{id}'",
            enable_cross_partition_query=True,
        )
        for item in response:
            return {
                "id": item["id"],
                "text": item["text"],
                "metadata": item["metadata"],
            }
        return {}


class GCPVectorDB(VectorDB):
    pass


class VectorDBFactory(Enum):
    local = ChromaVectorDB
    azure = AzureCosmosVectorDB
    gcp = GCPVectorDB
