from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    age: int
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    age: int
    phone: str | None
    address: str | None
    city: str | None
    country: str | None
    plan: str
    has_binance_keys: bool

    model_config = {"from_attributes": True}


class BinanceKeysRequest(BaseModel):
    api_key: str
    secret: str
