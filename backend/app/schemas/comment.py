from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CommentAuthorBrief(ORMModel):
    id: int
    first_name: str
    last_name: str
    email: str


class CommentOut(ORMModel):
    id: int
    case_id: int
    author_id: int
    comment_type: str
    text: str
    created_at: datetime
    author: CommentAuthorBrief | None = None


class CommentCreate(BaseModel):
    text: str = Field(min_length=1)
    comment_type: str = Field(default="GENERAL", pattern="^(GENERAL|QUESTION|ANSWER|INTERNAL)$")
