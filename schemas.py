from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterRole(str, Enum):
    PLAYER = "PLAYER"
    COACH = "COACH"


class PositionEnum(str, Enum):
    PG = "PG"
    SG = "SG"
    SF = "SF"
    PF = "PF"
    C = "C"


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


# --- School Schemas ---

class SchoolCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    location: str | None = Field(None, max_length=150)
    description: str | None = None
    logo_url: str | None = None


class SchoolUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=150)
    location: str | None = Field(None, max_length=150)
    description: str | None = None
    logo_url: str | None = None


class SchoolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str | None = None
    description: str | None = None
    logo_url: str | None = None
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


# --- Player Profile Schemas ---

class PlayerProfileCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: date | None = None
    height: float | None = Field(None, gt=0, description="Height must be greater than 0")
    weight: float | None = Field(None, gt=0, description="Weight must be greater than 0")
    position: PositionEnum
    jersey_number: int | None = Field(None, ge=0, le=99)
    school_id: int | None = None
    bio: str | None = None
    profile_image_url: str | None = None


class PlayerProfileUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=50)
    last_name: str | None = Field(None, min_length=1, max_length=50)
    date_of_birth: date | None = None
    height: float | None = Field(None, gt=0)
    weight: float | None = Field(None, gt=0)
    position: PositionEnum | None = None
    jersey_number: int | None = Field(None, ge=0, le=99)
    school_id: int | None = None
    bio: str | None = None
    profile_image_url: str | None = None


class PlayerProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    height: float | None = None
    weight: float | None = None
    position: str
    jersey_number: int | None = None
    school_id: int | None = None
    school: SchoolOut | None = None
    bio: str | None = None
    profile_image_url: str | None = None
    created_at: datetime
    updated_at: datetime


# --- Team Schemas ---

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    school_id: int
    description: str | None = None


class TeamUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=150)
    description: str | None = None


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    school_id: int
    description: str | None = None
    school: SchoolOut | None = None
    created_at: datetime
    updated_at: datetime


# --- Team Membership / Roster Schemas ---

class TeamMembershipCreate(BaseModel):
    player_id: int
    jersey_number: int | None = Field(None, ge=0, le=99)
    start_date: date | None = None
    is_active: bool = True


class TeamMembershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    player_id: int
    jersey_number: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool


class RosterMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    player_id: int
    player: PlayerProfileOut
    jersey_number: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool