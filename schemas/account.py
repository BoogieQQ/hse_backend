from pydantic import BaseModel, Field
from typing import Optional

class Account(BaseModel):
    id: int
    login: str
    password: Optional[str] = None
    is_blocked: bool = False
    
class AccountCreate(BaseModel):
    login: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    
class AccountResponse(BaseModel):
    id: int
    login: str
    is_blocked: bool

class AccountLogin(BaseModel):
    login: str = Field(...)
    password: str = Field(...)
    
class AccountBlockResponse(BaseModel):
    id: int
    login: str
    is_blocked: bool
    message: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
