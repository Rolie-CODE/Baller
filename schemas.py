from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    school: str


class UserLogin(BaseModel):
    username: str
    password: str