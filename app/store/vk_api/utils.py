import json
from logging import getLogger


class VkButton:
    def __init__(
        self,
        label: str,
        color: str = "primary",
        payload: str | dict | None = None,
        type_btn: str = "text",
    ):
        self.color = color
        self.label = label
        self.payload = None
        self.type_btn = type_btn
        if isinstance(payload, dict):
            self.payload = json.dumps(payload)

    def get(self):
        return {
            "action": {
                "type": self.type_btn,
                "payload": self.payload,
                "label": self.label,
            },
            "color": self.color,
        }


class VkKeyboard:
    _max_width = 5
    _max_lines = 10
    _max_buttons = 40

    def __init__(self, one_time: bool = False, inline: bool = False):
        self.keyboard = {"one_time": one_time, "buttons": [], "inline": inline}
        self.buttons = 0
        self.logger = getLogger("VkKeyboard")

    async def add_line(self, buttons: list[dict]):
        if len(buttons) > self._max_width:
            raise ValueError(
                "Слишком много кнопок в ряде: должно быть меньше: %s ",
                self._max_width,
            )
        if len(self.keyboard["buttons"]) > self._max_lines:
            raise ValueError("Слишком много рядов кнопок: %s ", self._max_lines)
        self.buttons += len(buttons)
        if self.buttons > self._max_buttons:
            raise ValueError(
                f"Слишком много кнопок: {self.buttons} > {self._max_buttons}"
            )

        self.keyboard["buttons"].append(buttons)

    async def get_keyboard(self):
        return json.dumps(self.keyboard, ensure_ascii=False)
