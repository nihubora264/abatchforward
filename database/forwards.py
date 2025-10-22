from beanie import Document, Link
from pydantic import Field
from datetime import datetime
from database.user import User
from typing import Optional


class Forward(Document):
    id: int = Field(alias="_id")
    user: Link[User]  # Link to the user who created this forward
    source_channel_id: int  # Source channel ID
    target_group_id: int  # Target group ID
    source_channel_title: Optional[str] = None  # Source channel title (optional for legacy data)
    target_group_title: Optional[str] = None  # Target group title (optional for legacy data)
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "forwards"