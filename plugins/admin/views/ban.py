from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from ..utils import get_admins
from ..views.user import user
from database.user import User

@Client.on_callback_query(filters.regex(r"^ban_user"))
async def ban_user(bot: Client, query: CallbackQuery):
    user_id = int(query.data.split()[1])
    _user = await User.find_one(User.id == user_id)
    if not _user:
        return await query.answer("No user found with this id!")
    admins = await get_admins()

    if user_id in admins:
        return await query.answer("You can't ban an admin!", show_alert=True)

    if _user.banned:
        await User.find_one(User.id == user_id).update({"banned": False})
        await query.answer("User unbanned successfully!")
    else:
        await User.find_one(User.id == user_id).update({"banned": True})
        await query.answer("User banned successfully!")

    query.data = f"user {user_id}"
    await user(bot, query)
