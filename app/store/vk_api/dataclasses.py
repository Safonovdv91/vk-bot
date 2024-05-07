from dataclasses import dataclass

import marshmallow_dataclass
from marshmallow import EXCLUDE


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


@dataclass
class LongPollResponse:
    ts: str
    updates: list[Update] = list

    class Meta:
        unknown = EXCLUDE


@dataclass
class SendMessage:
    peer_id: int
    text: str | None = None


ClientInfoSchema = marshmallow_dataclass.class_schema(ClientInfo)
MessageSchema = marshmallow_dataclass.class_schema(Message)
ObjectSchema = marshmallow_dataclass.class_schema(Object)
UpdateSchema = marshmallow_dataclass.class_schema(Update)
LongPollResponseSchema = marshmallow_dataclass.class_schema(LongPollResponse)
