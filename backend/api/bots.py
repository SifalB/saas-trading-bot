import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.bot import Bot
from backend.models.user import User
from backend.schemas.bot import BotCreate, BotResponse, BotUpdate, DEFAULT_CONFIGS
from backend.services.bot_runner import run_bot
from backend.workers import task_manager
from .deps import get_current_user

router = APIRouter(prefix="/bots", tags=["bots"])

MAX_BOTS_FREE = 1


@router.get("/defaults/{bot_type}")
async def get_default_config(bot_type: str):
    if bot_type not in DEFAULT_CONFIGS:
        raise HTTPException(status_code=404, detail="Unknown bot type")
    return DEFAULT_CONFIGS[bot_type]


@router.get("/", response_model=list[BotResponse])
async def list_bots(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Bot).where(Bot.user_id == current_user.id))
    return result.scalars().all()


@router.post("/", response_model=BotResponse, status_code=201)
async def create_bot(
    body: BotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.plan == "free":
        result = await db.execute(select(Bot).where(Bot.user_id == current_user.id))
        if len(result.scalars().all()) >= MAX_BOTS_FREE:
            raise HTTPException(status_code=403, detail="Free plan limited to 1 bot. Upgrade to Pro.")

    if body.type not in ("grid", "scalp", "corr"):
        raise HTTPException(status_code=400, detail="Invalid bot type. Use: grid | scalp | corr")

    # Merge with defaults so missing keys are filled in
    config = {**DEFAULT_CONFIGS[body.type], **body.config}
    bot = Bot(user_id=current_user.id, name=body.name, type=body.type,
              config=config, paper_mode=body.paper_mode)
    db.add(bot)
    await db.commit()
    await db.refresh(bot)
    return bot


@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: int,
    body: BotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = await _get_owned_bot(bot_id, current_user.id, db)
    if task_manager.is_running(bot_id):
        raise HTTPException(status_code=400, detail="Stop the bot before editing it.")
    if body.name is not None:
        bot.name = body.name
    if body.config is not None:
        bot.config = {**bot.config, **body.config}
    if body.paper_mode is not None:
        bot.paper_mode = body.paper_mode
    await db.commit()
    await db.refresh(bot)
    return bot


@router.delete("/{bot_id}", status_code=204)
async def delete_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = await _get_owned_bot(bot_id, current_user.id, db)
    task_manager.stop(bot_id)
    await db.delete(bot)
    await db.commit()


@router.post("/{bot_id}/start", status_code=204)
async def start_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bot = await _get_owned_bot(bot_id, current_user.id, db)
    if task_manager.is_running(bot_id):
        raise HTTPException(status_code=400, detail="Bot is already running.")
    if not bot.paper_mode and not current_user.binance_api_key:
        raise HTTPException(status_code=400, detail="Add your Binance API keys before running live.")
    task_manager.start(bot_id, lambda: run_bot(bot_id))


@router.post("/{bot_id}/stop", status_code=204)
async def stop_bot(
    bot_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_bot(bot_id, current_user.id, db)
    task_manager.stop(bot_id)


@router.websocket("/{bot_id}/logs")
async def bot_logs_ws(bot_id: int, websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    q = task_manager.get_log_queue(bot_id)
    if not q:
        await websocket.send_text("Bot is not running.")
        await websocket.close()
        return
    try:
        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=30)
                await websocket.send_text(msg)
            except asyncio.TimeoutError:
                await websocket.send_text("ping")
    except WebSocketDisconnect:
        pass


# ── Helper ────────────────────────────────────────────────────────────────────

async def _get_owned_bot(bot_id: int, user_id: int, db: AsyncSession) -> Bot:
    bot = await db.get(Bot, bot_id)
    if not bot or bot.user_id != user_id:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot
