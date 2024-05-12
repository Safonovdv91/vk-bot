from enum import Enum

from app.store.vk_api.utils import VkButton


class VkButtons(Enum):
    BTN_STOP_GAME = VkButton(label="Стоп игра", color="primary")
    BTN_REG_ON = VkButton(
        label="Буду играть",
        type_btn="callback",
        payload={"type": "show_snackbar", "text": "REG_ON"},
        color="secondary",
    )
    BTN_REG_OFF = VkButton(
        label="Отменить регистрацию",
        type_btn="callback",
        payload={"type": "show_snackbar", "text": "REG_OFF"},
    )
    BTN_ANSWER = VkButton(
        label="Знаю ответ!",
        type_btn="callback",
        payload={"type": "show_snackbar", "text": "Give answer"},
    )
