from dataclasses import dataclass
from typing import ClassVar

from marshmallow import EXCLUDE, Schema
from marshmallow_dataclass import dataclass as ms_dataclass


@dataclass
class ClientInfo:
    button_actions: list[str]

    class Meta:
        unknown = EXCLUDE


@dataclass
class Message:
    date: int
    from_id: int
    conversation_message_id: int
    peer_id: int
    text: str

    class Meta:
        unknown = EXCLUDE


@dataclass
class Object:
    message: Message | None = None
    client_info: ClientInfo | None = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class Update:
    group_id: int
    type: str
    event_id: str
    v: str
    object: Object

    class Meta:
        unknown = EXCLUDE


@ms_dataclass
class LongPollResponse:
    ts: str | None = None
    updates: list[Update] = list
    Schema: ClassVar[type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class SendMessage:
    peer_id: int
    text: str | None = ""


@dataclass
class SendMessageWithKeyboard(SendMessage):
    keyboard: str = None


@dataclass
class SendEditMessage(SendMessage):
    message_id: int = 0
