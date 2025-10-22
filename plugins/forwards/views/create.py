from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from plugins.account.utils.helpers import get_client_by_user_id
from ..utils.helpers import create_forward
from ..utils.buttons import get_add_channel_button, get_add_group_button
import logging
from bot.config import Config

logger = logging.getLogger(__name__)


@Client.on_message(filters.command("addforward") & filters.private & filters.incoming)
@Client.on_callback_query(filters.regex("^create_forward$"))
async def create_forward_callback(bot: Client, query: CallbackQuery | Message):
    """Handle create forward callback"""
    if isinstance(query, CallbackQuery):
        message = query.message
        message.from_user = query.from_user
        await create_forward_handler(bot, message)
    else:
        await create_forward_handler(bot, query)


async def create_forward_handler(bot: Client, message: Message, text: str = None):
    """Handle forward creation process"""
    buttons = [
        [get_add_channel_button()],
        [
            KeyboardButton(
                "Cancel",
            )
        ],
    ]
    if text is None:
        text = "Select the source of the forward"
    return await message.reply_text(
        text, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )


@Client.on_message(filters.chat_shared)
async def chat_shared(bot: Client, message: Message):
    button_id = message.chat_shared.button_id
    chat_id = message.chat_shared.chat.id
    user_id = message.from_user.id
    if button_id == 1:
        buttons = [
            [get_add_group_button(chat_id)],
            [
                KeyboardButton(
                    "Cancel",
                )
            ],
        ]
        user_joined = await is_user_joined(bot, user_id, chat_id)
        if not user_joined:
            return

        text = "✅ You have successfully selected the source channel. \n\nSelect the target of the forward"
        return await message.reply_text(
            text, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
        )
    else:
        if button_id not in Config.BUTTON_ID_CACHE:
            return await create_forward_handler(bot, message, text="❗️ Please try again from the start")
        
        out = await bot.send_message(user_id, "Please wait...", reply_markup=ReplyKeyboardRemove())
        source_id = Config.BUTTON_ID_CACHE[button_id]
        target_id = chat_id

        source_title = await get_chat_title_by_user_client(bot, user_id, source_id)
        if not source_title:
            return

        target_chat = await bot.get_chat(target_id)
        target_title = target_chat.title

        forward = await create_forward(
            user_id,
            source_id,
            target_id,
            source_title,
            target_title,
        )

        markup = InlineKeyboardMarkup(
            [
                # [InlineKeyboardButton("🔄 Index Channel", callback_data=f"batch_confirm_{forward}")],
                [InlineKeyboardButton("📋 My Forwards", callback_data="my_forwards")],
                [InlineKeyboardButton("⬅️ Back", callback_data="start")],
            ]
        )

        if forward is None:
            return await message.reply_text(
                "❗️ Forward already exists",
                reply_markup=markup,
            )

        await message.reply_text(
            f"✅ Forward created successfully for {source_title} → {target_title}",
            reply_markup=markup,
        )
        await out.delete()


async def is_user_joined(bot: Client, user_id: int, chat_id: int, get_chat: bool = False):
    user_client: Client = await get_client_by_user_id(user_id)
    if user_client:
        try:
            user_joined = await user_client.get_chat_member(chat_id, user_id)
            if get_chat:
                return await user_client.get_chat(chat_id)
            return True
        except Exception as e:
            await bot.send_message(
                user_id,
                f"❗️ Please make sure {user_client.me.first_name} (@{user_client.me.username}) has joined the channel and try again.",
            )
            return False

    await bot.send_message(
        user_id,
        f"❗️ Please login to your account and try again.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Login", callback_data="connect_account")]]
        ),
    )
    return False

async def get_chat_title_by_user_client(bot: Client, user_id: int, chat_id: int):
    user_joined = await is_user_joined(bot, user_id, chat_id, get_chat=True)
    if user_joined:
        return user_joined.title
    return None
