from pydantic import BaseModel
from datetime import datetime

class MessageOut(BaseModel):
    id: int
    room: str
    username: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


