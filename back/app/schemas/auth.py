from pydantic import BaseModel, EmailStr, Field

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone_number: str = Field(..., example="+380991234567", description="Номер телефона пользователя")
    is_active: bool = True