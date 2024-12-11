from enum import Enum


class VkMessagesMethods(Enum):
    send_event_answer = "messages.sendMessageEventAnswer"
    edit = "messages.edit"
    unpin = "messages.unpin"
    pin = "messages.pin"
    send = "messages.send"
    get = "users.get"
    send_reaction = "messages.sendReaction"



API_PATH = "https://api.vk.com/method/"
API_VERSION = "5.131"
VK_METHOD_ACT = "a_check"
VK_METHOD_WAIT = 25
