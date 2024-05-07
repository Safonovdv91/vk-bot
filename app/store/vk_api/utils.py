import json
from typing import Optional, Union


class VkButton:
    def __init__(
            self,
            label: str,
            color: str = "primary",
            payload: Optional[Union[str, dict]] = None,
            type_btn: str = "text"
    ):
        self.color = color
        self.label = label
        self.payload = None
        self.type = type_btn
        if isinstance(payload, dict):
            self.payload = json.dumps(payload)

    def get(self):
        button = {
            "action": {
                "type": "text",
                "payload": self.payload,
                "label": self.label
            },
            "color": self.color,
        }
        return button


class VkKeyboard:
    _max_width = 5
    _max_lines = 10
    _max_buttons = 40

    def __init__(self, one_time: bool = False, inline: bool = False):
        self.keyboard = {
            "one_time": one_time,
            "buttons": [],
            "inline": inline
        }

    def add_line(self, buttons: list[dict]):
        self.keyboard["buttons"].append(buttons)

    def get_keyboard(self):
        return json.dumps(self.keyboard, ensure_ascii=False)


if __name__ == "__main__":
    # Пример использования:
    vk_keyboard = VkKeyboard(one_time=True)

    btn1 = VkButton(label="Большая кнопка", color="primary")
    # print(btn1.get())
    #
    # vk_keyboard.add_line(
    #     [vk_keyboard.add_button(label="Большая кнопка", color="primary"), btn1.get()]
    # )
    #
    # Получение JSON-строки клавиатуры для отправки через VK API
    keyboard_json = vk_keyboard.get_keyboard()
    print(keyboard_json)
