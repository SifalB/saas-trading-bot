from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.core.security import create_access_token, decrypt, encrypt, hash_password, verify_password
from backend.models.user import User
from backend.schemas.auth import BinanceKeysRequest, LoginRequest, RegisterRequest, TokenResponse, UserResponse
from .deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/setup-needed")
async def setup_needed(db: AsyncSession = Depends(get_db)):
    """True when no owner account exists yet (first-run setup is available)."""
    result = await db.execute(select(User.id).limit(1))
    return {"setup_needed": result.first() is None}


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Single-user app: registration creates the owner account once, then locks.
    existing = await db.execute(select(User.id).limit(1))
    if existing.first() is not None:
        raise HTTPException(status_code=403, detail="This instance already has an owner. Sign in instead.")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        has_binance_keys=bool(current_user.binance_api_key),
    )


@router.put("/binance-keys", status_code=204)
async def set_binance_keys(
    body: BinanceKeysRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.binance_api_key = encrypt(body.api_key)
    current_user.binance_secret = encrypt(body.secret)
    await db.commit()
