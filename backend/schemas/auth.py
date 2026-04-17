from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    plan: str
    has_binance_keys: bool

    model_config = {"from_attributes": True}


class BinanceKeysRequest(BaseModel):
    api_key: str
    secret: str
