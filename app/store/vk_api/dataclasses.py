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
class Payload:
    type: str
    text: str


@dataclass
class VkObject:
    user_id: int | None = None
    peer_id: int | None = None
    event_id: str | None = None
    payload: Payload | None = None
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
    object: VkObject

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
class VkMessage:
    conversation_message_id: int
    date: int
    from_id: int
    peer_id: int
    text: str


@dataclass
class MessageObject:
    message: VkMessage


@dataclass
class EventPayload:
    text: str
    type: str


@dataclass
class EventObject:
    event_id: str
    payload: EventPayload
    peer_id: int
    user_id: int


@dataclass
class MessageUpdate:
    event_id: str
    group_id: int
    object: MessageObject


@dataclass
class EventUpdate:
    event_id: str
    group_id: int
    type: str
    object: EventObject


@dataclass
class VkUser:
    id: int
    first_name: str
    last_name: str

    def __repr__(self):
        return f"{self.first_name} {self.last_name}"
