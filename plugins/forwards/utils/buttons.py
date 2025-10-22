from pyrogram.types import KeyboardButton, KeyboardButtonRequestChat, ChatPrivileges
from bot.config import Config
import random

def get_add_channel_button() -> KeyboardButton:
    return KeyboardButton(
        "➕ Add Source Channel",
        request_chat=KeyboardButtonRequestChat(
            chat_is_channel=True,
            button_id=1,
        ),
    )


def get_add_group_button( chat_id: int) -> KeyboardButton:
    button_id = random.randint(100000, 999999)
    Config.BUTTON_ID_CACHE[button_id] = chat_id
    return KeyboardButton(
        "➕ Add Target Group",
        request_chat=KeyboardButtonRequestChat(
            chat_is_forum=True,
            chat_is_channel=False,
            button_id=button_id,
            bot_administrator_rights=ChatPrivileges(),
            user_administrator_rights=ChatPrivileges(),
        ),
    )
