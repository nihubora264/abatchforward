from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.forwards import Forward
from database.user import User
from typing import Optional, List
import logging
from plugins.common.utils.search import search_user_forwards

logger = logging.getLogger(__name__)    

async def get_source_channel(bot: Client, chat_id: int, user_id: int):
    try:
        return await bot.get_chat(chat_id)
    except Exception as e:
        await bot.send_message(
            user_id,
            f"❌ Make sure @{bot.me.username} is an admin of {chat_id} or it's a valid channel.",
        )
        return None


async def get_user_forwards_for_batch(user_id: int):
    """Get all forwards for a specific user for batch operations"""
    user = await User.find_one(User.id == user_id)
    if not user:
        return []

    forwards = await Forward.find(
        Forward.user.id == user_id, Forward.active == True
    ).to_list()
    return forwards


async def get_forward_by_id(forward_id: int, user_id: int) -> Optional[Forward]:
    """Get a specific forward by ID for a user"""
    forward = await Forward.find_one(
        Forward.id == forward_id, Forward.user.id == user_id, Forward.active == True
    )
    return forward


def create_batch_forwards_keyboard(
    forwards: List[Forward], page: int = 0, per_page: int = 10
) -> InlineKeyboardMarkup:
    """Create inline keyboard for batch forwards list with pagination"""
    keyboard = []

    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_forwards = forwards[start_idx:end_idx]

    # append a Current Batch button
    keyboard.append(
        [InlineKeyboardButton("🔄 Current Batch", callback_data="batch_current")]
    )

    for forward in page_forwards:
        text = f"📡 {forward.source_channel_title}"
        keyboard.append(
            [InlineKeyboardButton(text, callback_data=f"batch_select_{forward.id}")]
        )

    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Previous", callback_data=f"batch_page_{page-1}")
        )
    if end_idx < len(forwards):
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"batch_page_{page+1}")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Action buttons
    keyboard.append([InlineKeyboardButton("🔎 Search", callback_data="batch_search")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="start")])

    return InlineKeyboardMarkup(keyboard)


def create_batch_selection_keyboard(forward_id: int):
    """Create keyboard for batch channel selection actions"""
    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 Index Channel", callback_data=f"batch_confirm_{forward_id}"
            )
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="batch_list"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)





def parse_message_input(message, source_channel_id) -> int:
    """Parse message link or ID and return message ID"""
    if message.forward_origin:
        return message.forward_origin.message_id

    try:
        # Check if it's a direct number
        if message.text.isdigit():
            return int(message.text)

        # Check if it's a Telegram message link
        if "t.me/" in message.text and "/" in message.text:
            if not check_if_link_is_valid(message.text, source_channel_id):
                return None
            # Extract message ID from link like https://t.me/channel/123
            parts = message.text.split("/")
            if len(parts) >= 2:
                message_id = parts[-1]
                if message_id.isdigit():
                    return int(message_id)

        return None
    except Exception as e:
        logger.error(f"Error parsing message input: {e}")
        return None


def check_if_link_is_valid(text: str, chat_id: int):
    """Check if the message link is from the correct channel"""
    if "://" not in text:
        return False

    if "/c/" in text:
        # extract the chat id from the text
        chat_id = int("-100" + text.split("/")[-2])
        return chat_id == chat_id
    else:
        return True # this is username whichw e cant check


async def prompt_start_message(query, forward, source_channel_id):
    """Prompt user for start message and return the message ID"""
    start_text = (
        f"📡 **Batch Indexing Setup**\n\n"
        f"**Channel:** {forward.source_channel_title}\n"
        f"**Target:** {forward.target_group_title}\n\n"
        f"📍 **Step 1: Start Message**\n\n"
        f"Send the **message link** or **forward message** where you want to start indexing.\n\n"
        f"You can also use:\n"
        f"• /skip - Start from the beginning of the channel\n\n"
        f"Example: `https://t.me/channel/123`"
    )

    await query.message.reply_text(start_text)

    try:
        start_response = await query.message.chat.ask(
            "💬 Send start message link or forward message or /skip:", timeout=300
        )

        if start_response.text == "/skip":
            return None

        try:
            start_message_id = parse_message_input(start_response, source_channel_id)
            if start_message_id is None:
                await start_response.reply(
                    "❌ Invalid message. Using channel beginning instead."
                )
                return None
            return start_message_id
        except Exception as e:
            logger.error(f"Error parsing message input: {e}")
            await start_response.reply(
                f"❌ Make sure {start_response.text} is from the {source_channel_id}"
            )
            return False

    except Exception as e:
        await query.message.reply("⏰ Timeout! Using channel beginning as start point.")
        return None


async def prompt_end_message(query, start_message_id, source_channel_id):
    """Prompt user for end message and return the message ID"""
    end_text = (
        f"📍 **Step 2: End Message**\n\n"
        f"Send the **message link** or **number of messages** or **forward message** where you want to stop indexing.\n\n"
        f"You can also use:\n"
        f"• `/skip` - Index until the latest message\n"
        f"• `/all` - Index all messages until the end\n\n"
        f"Example: `https://t.me/channel/456` or `100`"
    )

    await query.message.reply_text(end_text)

    try:
        end_response = await query.message.chat.ask(
            "💬 Send end message link or number of messages, forward message, /skip, or /all:",
            timeout=300,
        )

        if end_response.text in ["/skip", "/all"]:
            return None
        elif end_response.text.isdigit():
            return start_message_id + int(end_response.text) if start_message_id else int(end_response.text)
        else:
            try:
                end_message_id = parse_message_input(end_response, source_channel_id)
                if end_message_id is None:
                    await end_response.reply(
                        "❌ Invalid message link/ID format. Using channel end instead."
                    )
                    return None
                return end_message_id
            except Exception as e:
                await end_response.reply(
                    f"❌ Make sure {end_response.text} is from the {source_channel_id}"
                )
                return False

    except Exception as e:

        await query.message.reply("⏰ Timeout! Using channel end as stop point.")
        return None


def create_confirmation_message(forward, start_message_id, end_message_id, forward_id):
    """Create the confirmation message and keyboard for batch indexing"""

    def make_message_link(chat_id, message_id):
        # Handles both public and private channels
        if str(chat_id).startswith("-100"):
            return f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"
        else:
            return f"https://t.me/{chat_id}/{message_id}"

    from_link = (
        make_message_link(forward.source_channel_id, start_message_id)
        if start_message_id else None
    )
    to_link = (
        make_message_link(forward.source_channel_id, end_message_id)
        if end_message_id else None
    )

    confirmation_text = (
        f"✅ **Batch Configuration Complete**\n\n"
        f"**Settings:** {forward.source_channel_title} -> {forward.target_group_title}\n\n"
        f"**From:** "
        f"{f'[Message {start_message_id}]({from_link})' if start_message_id else 'Beginning of channel'}\n"
        f"**To:** "
        f"{f'[Message {end_message_id}]({to_link})' if end_message_id else 'Latest message'}\n\n"
        f"🔄 Ready to start batch indexing!"
    )

    callback_data = (
        f"batch_index_{forward_id}_{start_message_id or 0}_{end_message_id or 0}"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Start Indexing", callback_data=callback_data)],
            [InlineKeyboardButton("❌ Cancel", callback_data="batch_list")],
        ]
    )

    return confirmation_text, keyboard


async def handle_batch_search(query) -> None:
    """Prompt the user for a search term and show results using the batch keyboard."""
    try:
        prompt_text = (
            "🔎 Search channels for forwards (source/target title).\n\n"
            "Type /cancel to abort."
        )
        # await query.message.reply_text(prompt_text)

        response = await query.message.chat.ask(prompt_text, timeout=180)

        if not response or not getattr(response, "text", None):
            await query.message.reply_text("❌ No input received.")
            return

        if response.text.strip().lower() == "/cancel":
            await response.reply("✅ Cancelled.")
            return

        user_id = query.from_user.id
        results = await search_user_forwards(user_id=user_id, query=response.text)

        if not results:
            await response.reply("⚠️ No forwards matched your search.")
            return

        keyboard = create_batch_forwards_keyboard(results, page=0, per_page=20)
        await response.reply_text(f"🔎 Search results: ({len(results)})", reply_markup=keyboard)
    except Exception as e:
        logger.exception("Error during batch search handling")
        await query.message.reply_text("❌ An error occurred while searching.")