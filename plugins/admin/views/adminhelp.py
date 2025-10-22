from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from bot.config import Config


@Client.on_message(
    filters.command("admin") & filters.private & filters.user(Config.OWNER_ID)
)
@Client.on_callback_query(filters.regex("^admin$"))
async def admin(client: Client, message: Message):
    text = (
        "👑 **Admin Panel**\n\n"
        "Here are the available admin commands:\n\n"
        "• /addadmin <user_id> — Add a new admin\n"
        "• /admins — List all admins\n"
        "• /removeadmin <user_id> — Remove an admin\n"
        "• /users — List all users\n"
        "• /user <user_id> — View user details, ban or unban a user\n"
        "• /broadcast — Send a broadcast message to all users\n\n"
        "Use these commands in a private chat with the bot. For more details on each command, use /help."
    )

    await client.reply(message, text, parse_mode=ParseMode.MARKDOWN)
