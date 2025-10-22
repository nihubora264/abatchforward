import functools
from pyrogram import Client
from database import Admin


async def get_or_create_admin(user_id):
    admin = await Admin.find_one(Admin.id == user_id)
    if admin:
        return admin, False
    admin = Admin(id=user_id)
    await admin.save()
    return admin, True


async def get_admins():
    admins = await Admin.find_all().to_list()
    return [admin.id for admin in admins]


async def add_admin(user_id):
    admin, is_new = await get_or_create_admin(user_id)
    if is_new:
        return True
    return False


async def remove_admin(user_id):
    await Admin.find_one(Admin.id == user_id).delete()
    return True


def check_admin(func):
    """Check if user is admin or not"""

    @functools.wraps(func)
    async def wrapper(client: Client, message):
        chat_id = getattr(message.from_user, "id", None)
        is_admin = await Admin.find_one(Admin.id == chat_id)

        if not is_admin:
            return await client.reply(
                message, "You are not allowed to use this command."
            )
        return await func(client, message)

    return wrapper
