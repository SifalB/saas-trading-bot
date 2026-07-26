import asyncio
import os
import sys

# asyncpg requires SelectorEventLoop on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.core.config import settings
from backend.core.database import init_db
from backend.api import auth, bots, trades, dashboard


async def _resume_running_bots() -> None:
    """Restart bots that were running before the process stopped.

    Running tasks live only in memory, so every deploy or restart silently
    killed them while the database still reported "running" — the dashboard
    showed active bots that no longer existed. Resuming here closes that gap.
    """
    from sqlalchemy import select

    from backend.core.database import AsyncSessionLocal
    from backend.models.bot import Bot
    from backend.services.bot_runner import run_bot
    from backend.workers import task_manager

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Bot).where(Bot.status == "running"))
        bots = result.scalars().all()

    for bot in bots:
        if not task_manager.is_running(bot.id):
            task_manager.start(bot.id, lambda bid=bot.id: run_bot(bid))
    if bots:
        print(f"Resumed {len(bots)} bot(s) after restart: {[b.name for b in bots]}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _resume_running_bots()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All API routes live under /api so they never collide with frontend routes
# (the app has its own /dashboard, /activity, ... pages) when served same-origin.
API_PREFIX = "/api"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(bots.router, prefix=API_PREFIX)
app.include_router(trades.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)


@app.get("/api/health")
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/diag/exchange")
async def diag_exchange():
    """Public reachability check: can this host pull Binance public data?"""
    import ccxt.async_support as ccxt

    ex = ccxt.binance({"options": {"defaultType": "spot"}})
    try:
        t = await ex.fetch_ticker("BTC/USDT")
        return {"ok": True, "exchange": "binance", "btc_usdt": t.get("last")}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "exchange": "binance", "error": str(e)[:400]}
    finally:
        await ex.close()


# ── Serve the exported Next.js frontend (single-instance deploy) ───────────────
# In the Docker image the static export is copied to FRONTEND_DIR. When it is
# absent (backend-only local dev), these routes simply don't get registered.
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", "frontend_static")).resolve()

if FRONTEND_DIR.is_dir():
    _INDEX = FRONTEND_DIR / "index.html"

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Never let the SPA catch-all shadow the API.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        # Resolve safely inside FRONTEND_DIR (block path traversal).
        try:
            target = (FRONTEND_DIR / full_path).resolve()
            target.relative_to(FRONTEND_DIR)
        except (ValueError, RuntimeError):
            raise HTTPException(status_code=404, detail="Not found")

        # 1) exact static asset (js/css/svg/…)
        if full_path and target.is_file():
            return FileResponse(target)
        # 2) exported route folder → route/index.html  (trailingSlash: true)
        page = target / "index.html"
        if page.is_file():
            return FileResponse(page)
        # 3) root
        if not full_path:
            return FileResponse(_INDEX)
        # 4) fallback to Next's 404 page, else the SPA shell
        not_found = FRONTEND_DIR / "404.html"
        if not_found.is_file():
            return FileResponse(not_found, status_code=404)
        return FileResponse(_INDEX)
