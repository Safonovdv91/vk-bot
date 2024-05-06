from dataclasses import dataclass


@dataclass
class VkPersonalMessageObject:
    date: int
    from_id: int
    peer_id: int
    id: int
    conversation_message_id: int
    text: str


@dataclass
class VkUpdate:
    group_id: int
    type: str
    event_id: str
    v: str
    vk_object: VkPersonalMessageObject


@dataclass
class Message:
    peer_id: int
    text: str
