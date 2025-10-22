from typing import List
import re

from database.forwards import Forward
from database.user import User
from beanie.operators import Or, RegEx


async def search_user_forwards(user_id: int, query: str) -> List[Forward]:
    """Search active forwards for a user by source or target titles (case-insensitive, partial).

    Returns a list of matching Forward documents.
    """
    if not query:
        return []

    # Load user first to ensure existence
    user = await User.find_one(User.id == user_id)
    if not user:
        return []

    # Case-insensitive partial search using MongoDB regex with OR over source/target titles
    q = query.strip()
    if not q:
        return []

    pattern = re.escape(q)

    results: List[Forward] = await Forward.find(
        Forward.user.id == user_id,
        Forward.active == True,
        Or(
            RegEx(Forward.source_channel_title, pattern, options="i"),
            RegEx(Forward.target_group_title, pattern, options="i"),
        ),
    ).to_list()

    return results


