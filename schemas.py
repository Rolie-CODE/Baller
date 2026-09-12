from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterRole(str, Enum):
    PLAYER = "PLAYER"
    COACH = "COACH"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: RegisterRole = RegisterRole.PLAYER


class UserLogin(BaseModel):
    username_or_email: str | None = None
    username: str | None = None
    email: str | None = None
    password: str = Field(..., min_length=1)

    def get_identifier(self) -> str | None:
        return self.username_or_email or self.username or self.email


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None
    email: str | None = None
    role: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime