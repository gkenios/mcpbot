from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel

from mcpbot.shared.utils import read_file, write_file


OrderBy = Literal["ASC", "DESC"]
Role = Literal["human", "ai"]


class Conversation(BaseModel):
    id: str
    user_id: str
    created_at: str
    last_updated_at: str


class Message(BaseModel):
    id: str
    conversation_id: str
    user_id: str
    role: Role
    text: str
    created_at: str


class ChatDB(ABC):
    def create_conversation(
        self, user_id: str, conversation_id: str | None = None
    ) -> Conversation:
        if not conversation_id:
            conversation_id = uuid4().hex
        timestamp = datetime.now(UTC).isoformat()
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            created_at=timestamp,
            last_updated_at=timestamp,
        )
        self._create_conversation(conversation)
        return conversation

    def create_message(
        self, conversation_id: str, user_id: str, role: Role, text: str
    ) -> Message:
        message_id = uuid4().hex
        timestamp = datetime.now(UTC).isoformat()
        message = Message(
            id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            text=text,
            created_at=timestamp,
        )
        self._create_message(message)
        return message

    def delete_over_n_messages(
        self,
        conversation_id: str,
        n_messages: int,
    ) -> None:
        messages = self.list_messages(conversation_id)
        if len(messages) > n_messages:
            for message_id in messages[n_messages:]:
                self.delete_message(message_id.id, conversation_id)

    def update_conversation_timestamp(
        self,
        conversation_id: str,
        user_id: str,
    ) -> None:
        conversation = self.get_conversation(conversation_id, user_id)
        if not conversation:
            return
        conversation.last_updated_at = datetime.now(UTC).isoformat()
        self._update_conversation(conversation)

    @abstractmethod
    def _create_conversation(self, conversation: Conversation) -> None:
        raise NotImplementedError

    @abstractmethod
    def _create_message(self, message: Message) -> None:
        raise NotImplementedError

    @abstractmethod
    def _update_conversation(self, conversation: Conversation) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_conversation(self, conversation_id: str, user_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_message(self, message_id: str, conversation_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_conversations(
        self, user_id: str, order_by: OrderBy = "DESC"
    ) -> list[Conversation]:
        raise NotImplementedError

    @abstractmethod
    def list_messages(
        self, conversation_id: str, order_by: OrderBy = "ASC"
    ) -> list[Message]:
        raise NotImplementedError

    @abstractmethod
    def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Conversation | None:
        raise NotImplementedError

    @abstractmethod
    def get_message(
        self, message_id: str, conversation_id: str
    ) -> Message | None:
        raise NotImplementedError


class JsonChatDB(ChatDB):
    def __init__(
        self,
        endpoint: str,
        collection: str,
        **kwargs: Any,
    ):
        self.path = f"{endpoint}/{collection}"

    def _create_conversation(self, conversation: Conversation) -> None:
        write_file(
            f"{self.path}/{conversation.user_id}/{conversation.id}.json",
            conversation.model_dump(),
        )

    def _create_message(self, message: Message) -> None:
        write_file(
            f"{self.path}/{message.conversation_id}/{message.id}.json",
            message.model_dump(),
        )

    def _update_conversation(self, conversation: Conversation) -> None:
        return self._create_conversation(conversation)

    def delete_conversation(self, conversation_id: str, user_id: str) -> None:
        file_path = Path(self.path) / user_id / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()

    def delete_message(self, message_id: str, conversation_id: str) -> None:
        file_path = Path(self.path) / conversation_id / f"{message_id}.json"
        if file_path.exists():
            file_path.unlink()

    def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Conversation | None:
        try:
            conversation = read_file(
                f"{self.path}/{user_id}/{conversation_id}.json"
            )
        except FileNotFoundError:
            return None
        return Conversation(**conversation)

    def get_message(
        self, message_id: str, conversation_id: str
    ) -> Message | None:
        try:
            message = read_file(
                f"{self.path}/{conversation_id}/{message_id}.json"
            )
        except FileNotFoundError:
            return None
        return Message(**message)

    def list_conversations(
        self,
        user_id: str,
        order_by: OrderBy = "DESC",
    ) -> list[Conversation]:
        conversations = Path(self.path) / user_id
        if not conversations.exists():
            return []
        for conversation in conversations.iterdir():
            if not conversation.is_file():
                continue

        listed_conversations = [
            Conversation(**read_file(conversation))
            for conversation in conversations.iterdir()
            if conversation.is_file()
        ]
        listed_conversations.sort(
            key=lambda x: x.created_at,
            reverse={"ASC": False, "DESC": True}[order_by],
        )
        return listed_conversations

    def list_messages(
        self,
        conversation_id: str,
        order_by: OrderBy = "ASC",
    ) -> list[Message]:
        messages = Path(self.path) / conversation_id
        if not messages.exists():
            return []
        listed_messages = [
            Message(**read_file(message))
            for message in messages.iterdir()
            if message.is_file()
        ]
        listed_messages.sort(
            key=lambda x: x.created_at,
            reverse={"ASC": False, "DESC": True}[order_by],
        )
        return listed_messages


class AzureCosmosChatDB(ChatDB):
    def __init__(
        self,
        database: str,
        collection: str,
        endpoint: str,
        api_key: str,
    ):
        from azure.cosmos import CosmosClient
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        self.client = (
            CosmosClient(endpoint, api_key)
            .get_database_client(database)
            .get_container_client(collection)
        )
        self.read_item_error = CosmosResourceNotFoundError

    def _create_conversation(self, conversation: Conversation) -> None:
        self.client.create_item(conversation.model_dump())

    def _create_message(self, message: Message) -> None:
        self.client.create_item(message.model_dump())

    def _update_conversation(self, conversation: Conversation) -> None:
        self.client.upsert_item(conversation.model_dump())

    def delete_conversation(self, conversation_id: str, user_id: str) -> None:
        self.client.delete_item(conversation_id, user_id)

    def delete_message(self, message_id: str, conversation_id: str) -> None:
        self.client.delete_item(message_id, conversation_id)

    def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Conversation | None:
        try:
            conversation = self.client.read_item(conversation_id, user_id)
        except self.read_item_error:
            return None
        return Conversation(**conversation)

    def get_message(
        self, message_id: str, conversation_id: str
    ) -> Message | None:
        try:
            message = self.client.read_item(message_id, conversation_id)
        except self.read_item_error:
            return None
        return Message(**message)

    def list_conversations(
        self,
        user_id: str,
        order_by: OrderBy = "DESC",
    ) -> list[Conversation]:
        conversations = self.client.query_items(
            f"SELECT * "
            f"FROM c WHERE c.user_id = '{user_id}' "
            f"ORDER BY c.last_updated_at {order_by}",
        )
        return [Conversation(**conversation) for conversation in conversations]

    def list_messages(
        self,
        conversation_id: str,
        order_by: OrderBy = "ASC",
    ) -> list[Message]:
        messages = self.client.query_items(
            f"SELECT * "
            f"FROM c WHERE c.conversation_id = '{conversation_id}' "
            f"ORDER BY c.created_at {order_by}",
        )
        return [Message(**message) for message in messages]


class GCPNoSQLDB(ChatDB):
    pass


def get_chat_db(endpoint: str, collection: str, **kwargs: Any) -> ChatDB:
    if "azure.com" in endpoint:
        return AzureCosmosChatDB(
            endpoint=endpoint,
            collection=collection,
            **kwargs,
        )
    else:
        return JsonChatDB(
            endpoint=endpoint,
            collection=collection,
            **kwargs,
        )
