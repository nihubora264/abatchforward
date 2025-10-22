from beanie import Document
from pydantic import Field


from datetime import datetime


class Admin(Document):
    id: int = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "admins"