from pyrogram import Client, filters, types
from ..utils.admin_manager import check_admin
from database.user import User

@Client.on_message(filters.command("user") & filters.private & filters.incoming)
@Client.on_callback_query(filters.regex("^user "))
@check_admin
async def user(bot: Client, message: types.Message | types.CallbackQuery):
    if isinstance(message, types.Message):
        if len(message.command) <= 1:
            return await message.reply_text(
                "Please specify a user id or username!\n\nExample: `/user 1234567890` or `/user @username`"
            )
        user_id = message.command[1]
        if user_id.isdigit():
            user_id = int(user_id)
        else:
            user_id = user_id.replace("@", "")
            try:
                user_id = (await bot.get_users(user_id)).id
            except Exception:
                return await message.reply_text("Invalid user id or username!")
        func = message.reply_text
    else:
        func = message.edit_message_text
        user_id = int(message.data.split()[1])

    user = await User.find_one(User.id == user_id)
    try:
        tg_user = await bot.get_users(user_id)
    except Exception:
        tg_user = None

    if not user:
        return await func("No user found with this id!")

    text = f"""
👤 **User Details**

ID: `{user.id}`
Username: {f"@{tg_user.username}" if tg_user and tg_user.username else 'Not Available'}
Banned: {'Yes' if user.banned else 'No'}
"""

    await func(
        text,
        reply_markup=types.InlineKeyboardMarkup(
            [
                # ban if not banned else unban
                [
                    types.InlineKeyboardButton(
                        "🚫 Ban" if not user.banned else "✅ Unban",
                        callback_data=f"ban_user {user.id}",
                    )
                ],
                [types.InlineKeyboardButton("⬅️ Back", callback_data="admin")],
            ],
        ),
    )
    return
