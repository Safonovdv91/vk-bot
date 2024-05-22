from enum import Enum

from app.store.vk_api.utils import VkButton


class VkButtons(Enum):
    BTN_STOP_GAME = VkButton(label="Стоп игра", color="primary").get()
    BTN_REG_ON = VkButton(
        label="Буду играть",
        type_btn="callback",
        payload={"type": "show_snackbar", "text": "/reg_on"},
        color="secondary",
    ).get()
    BTN_REG_OFF = VkButton(
        label="Отменить регистрацию",
        type_btn="callback",
        payload={"type": "show_snackbar", "text": "/reg_off"},
    ).get()
    BTN_ANSWER = VkButton(
        label="Знаю ответ!",
        type_btn="callback",
        payload={"type": "show_snackbar", "text": "/give_answer"},
    ).get()
