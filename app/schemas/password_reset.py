#  app/schemas/password_reset.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordResetResponse(BaseModel):
    message: str
    success: bool