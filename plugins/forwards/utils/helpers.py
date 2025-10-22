from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.forwards import Forward
from database.user import User
import random
from plugins.common.utils.search import search_user_forwards


async def get_user_forwards(user_id: int):
    """Get all forwards for a specific user"""
    user = await User.find_one(User.id == user_id)
    if not user:
        return []

    forwards = await Forward.find(
        Forward.user.id == user_id, Forward.active == True
    ).to_list()
    return forwards


async def get_forward_by_id(forward_id: int, user_id: int):
    """Get a specific forward by ID for a user"""
    forward = await Forward.find_one(
        Forward.id == forward_id, Forward.user.id == user_id, Forward.active == True
    )
    return forward


async def create_forward(
    user_id: int,
    source_channel_id: int,
    target_group_id: int,
    source_channel_title: str,
    target_group_title: str,
):
    """Create a new forward"""
    user = await User.find_one(User.id == user_id)
    if not user:
        return None

    # Check if forward already exists
    existing = await Forward.find_one(
        Forward.user.id == user_id,
        Forward.source_channel_id == source_channel_id,
        Forward.target_group_id == target_group_id,
        Forward.active == True,
    )

    if existing:
        return None  # Already exists
    forward_id = random.randint(1000000000, 9999999999)
    forward = Forward(
        id=forward_id,
        user=user,
        source_channel_id=source_channel_id,
        target_group_id=target_group_id,
        source_channel_title=source_channel_title,
        target_group_title=target_group_title,
        active=True,
    )
    await forward.save()
    return forward_id


async def delete_forward(forward_id: int, user_id: int):
    """Delete a forward (soft delete by setting active=False)"""
    forward = await Forward.find_one(
        Forward.id == forward_id, Forward.user.id == user_id, Forward.active == True
    )

    if forward:
        forward.active = False
        await forward.save()
        return True
    return False


def create_forwards_keyboard(forwards, page=0, per_page=5):
    """Create inline keyboard for forwards list with pagination"""
    keyboard = []

    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_forwards = forwards[start_idx:end_idx]

    for forward in page_forwards:
        text = f"{forward.source_channel_title} → {forward.target_group_title}"
        keyboard.append(
            [InlineKeyboardButton(text, callback_data=f"view_forward_{forward.id}")]
        )

    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Previous", callback_data=f"forwards_page_{page-1}")
        )
    if end_idx < len(forwards):
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"forwards_page_{page+1}")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)
    # Actions row 1
    keyboard.append([
        InlineKeyboardButton("🔎 Search", callback_data="forwards_search"),
        InlineKeyboardButton("➕ Add Forward", callback_data="create_forward"),
    ])
    # Actions row 2
    keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data="start"),
    ])
    # Action buttons
    # keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="start")])

    return InlineKeyboardMarkup(keyboard)


def create_forward_detail_keyboard(forward_id: int):
    """Create keyboard for individual forward view"""
    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 Index Channel", callback_data=f"batch_confirm_{forward_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🗑️ Delete Forward", callback_data=f"delete_forward_{forward_id}"
            )
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="my_forwards"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_delete_confirmation_keyboard(forward_id: int):
    """Create confirmation keyboard for delete action"""
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Confirm Delete", callback_data=f"confirm_delete_{forward_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Cancel", callback_data=f"view_forward_{forward_id}"
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def handle_forwards_search(query) -> None:
    """Prompt the user for a search term and show results using the forwards keyboard."""
    try:
        prompt_text = (
            "🔎 Send search text for forwards (source/target title).\n\n"
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

        keyboard = create_forwards_keyboard(results, page=0, per_page=20)
        await response.reply_text(f"Search results: ({len(results)})", reply_markup=keyboard)
    except Exception:
        await query.message.reply_text("❌ An error occurred while searching.")
