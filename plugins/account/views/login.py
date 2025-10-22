from pyrogram.types import Message
from pyrogram import Client, filters
from asyncio.exceptions import TimeoutError
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
    CallbackQuery,
)
from pyrogram.errors import (
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
)
from database import Session, User
from bot import User as UserClient

class Data:
    generate_single_button = [
        InlineKeyboardButton("🔐 Login", callback_data="connect_account")
    ]

    home_buttons = [
        [InlineKeyboardButton("🔐 Account", callback_data="connected_account")],
        [InlineKeyboardButton("⬅️ Back", callback_data="start")],
    ]

    generate_button = [generate_single_button]


@Client.on_callback_query(filters.regex("^connect_account$"))
async def connect_account(bot: Client, message: CallbackQuery):
    user_message = message.message
    user_message.from_user = message.from_user
    await generate_session(bot, user_message)


async def generate_session(bot: Client, msg: Message):

    user_id = msg.from_user.id

    api_id = bot.api_id
    api_hash = bot.api_hash

    t = "📱 **Send your phone number**\n\nExample: `+19876543210`\n\n/cancel to cancel"

    phone_number_msg: Message = await bot.ask(
        user_id,
        t,
        filters=filters.text | filters.contact,
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Send Phone Number", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
        timeout=300,
    )
    if await cancelled(phone_number_msg):
        return

    if phone_number_msg.contact:
        phone_number = phone_number_msg.contact.phone_number
    else:
        phone_number = phone_number_msg.text

    await msg.reply("🔐 **Connecting...**", reply_markup=ReplyKeyboardRemove())

    client = Client(
        name=f"user_{user_id}", api_id=api_id, api_hash=api_hash, in_memory=True
    )

    await client.connect()
    try:
        code = None
        code = await client.send_code(phone_number)
    except PhoneNumberInvalid:
        await msg.reply(
            "❌ **Invalid phone number**\n\nPlease try again.",
            reply_markup=InlineKeyboardMarkup(Data.generate_button),
        )
        return
    try:
        phone_code_msg = None
        phone_code_msg = await bot.ask(
            user_id,
            "📱 **Enter verification code**\n\nCheck your Telegram app for the code.\nSend it with spaces: `1 2 3 4 5`",
            filters=filters.text,
            timeout=600,
        )
        if await cancelled(phone_code_msg):
            return
    except TimeoutError:
        await msg.reply(
            "⏰ **Time expired**\n\nPlease try again.",
            reply_markup=InlineKeyboardMarkup(Data.generate_button),
        )
        return

    if " " not in phone_code_msg.text:
        await phone_code_msg.reply(
            "❌ **Invalid format**\n\nSend code with spaces: `1 2 3 4 5`",
            quote=True,
            reply_markup=InlineKeyboardMarkup(Data.generate_button),
        )
        return

    phone_code = phone_code_msg.text.replace(" ", "")
    try:
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        await msg.reply(
            "❌ **Invalid code**\n\nPlease try again.",
            reply_markup=InlineKeyboardMarkup(Data.generate_button),
        )
        return
    except PhoneCodeExpired:
        await msg.reply(
            "⏰ **Code expired**\n\nPlease try again.",
            reply_markup=InlineKeyboardMarkup(Data.generate_button),
        )
        return
    except SessionPasswordNeeded:
        try:
            two_step_msg = await bot.ask(
                user_id,
                "🔐 **Enter 2FA password**\n\nYour account has two-step verification enabled.",
                filters=filters.text,
                timeout=300,
            )
        except TimeoutError:
            await msg.reply(
                "⏰ **Time expired**\n\nPlease try again.",
                reply_markup=InlineKeyboardMarkup(Data.generate_button),
            )
            return
        try:
            password = two_step_msg.text
            await client.check_password(password=password)
        except PasswordHashInvalid:
            await two_step_msg.reply(
                "❌ **Invalid password**\n\nPlease try again.",
                quote=True,
                reply_markup=InlineKeyboardMarkup(Data.generate_button),
            )
            return

    string_session = await client.export_session_string()
    me = await client.get_me()

    user = await User.find_one(User.id == user_id)

    session = Session(
        id=me.id,
        user=user,
        session_string=string_session,
        username=me.username,
    )
    
    await session.save()

    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Add Forward", callback_data="create_forward")],
            [InlineKeyboardButton("📤 My Forwards", callback_data="my_forwards")],
            [InlineKeyboardButton("⬅️ Back", callback_data="start")],
        ]
    )

    await bot.send_message(
        msg.chat.id,
        "✅ **Login successful**\n\nYour account is now connected.",
        reply_markup=markup,
    )

    client = UserClient(string_session, name=f"user_{user_id}")
    await client.start()


async def cancelled(msg: Message):
    if not msg.text:
        return
    if "/cancel" in msg.text:
        await msg.reply(
            "❌ **Login cancelled**",
            quote=True,
            reply_markup=ReplyKeyboardRemove(),
        )
        await msg.reply(
            "You can try logging in again.",
            quote=True,
            reply_markup=InlineKeyboardMarkup(Data.generate_button),
        )
        return True
    elif msg.text.startswith("/"):  # Bot Commands
        await msg.reply(
            "❌ **Login cancelled**",
            quote=True,
            reply_markup=ReplyKeyboardRemove(),
        )
        return True
    else:
        return False
