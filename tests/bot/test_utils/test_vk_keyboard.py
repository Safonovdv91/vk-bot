import asyncio

import pytest

from app.store.vk_api.utils import VkButton, VkKeyboard


class TestCreateVkKeyboard:
    async def test_success(
        self,
    ) -> None:
        keyboard = VkKeyboard(one_time=False)
        btn1 = VkButton("test_btn")
        await keyboard.add_line(btn1.get())
        keyboard_json = await keyboard.get_keyboard()
        test_keyboard_json = (
            '{"one_time": false, "buttons": '
            '[{"action": {"type": "text", "payload": null,'
            ' "label": "test_btn"}, "color": "primary"}], "inline": false}'
        )
        assert keyboard_json == test_keyboard_json

    async def test_many_so_many_buttons_in_line(self) -> None:
        keyboard = VkKeyboard(one_time=False)
        btn_list = [VkButton(f"test_btn{i}").get() for i in range(6)]
        with pytest.raises(
            ValueError,
            match=r"Слишком много кнопок в ряде: должно быть меньше:",
        ):
            await keyboard.add_line(btn_list)

    async def test_many_so_many_lines(self) -> None:
        keyboard = VkKeyboard(one_time=False)
        btn_list = [VkButton(f"test_btn{i}").get() for i in range(3)]
        tasks = [keyboard.add_line(btn_list) for _ in range(11)]
        await asyncio.gather(*tasks)
        with pytest.raises(ValueError, match=r"Слишком много рядов кнопок"):
            await keyboard.add_line([VkButton("OneMoreButton").get()])

    async def test_many_so_many_buttons(self) -> None:
        keyboard = VkKeyboard(one_time=False)
        btn_list = [VkButton(f"test_btn{i}").get() for i in range(5)]
        tasks = [keyboard.add_line(btn_list) for _ in range(8)]
        await asyncio.gather(*tasks)
        with pytest.raises(ValueError, match=r"Слишком много кнопок"):
            await keyboard.add_line([VkButton("OneMoreButton").get()])
