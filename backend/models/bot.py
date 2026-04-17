from datetime import datetime, UTC

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)   # grid | scalp | corr
    config: Mapped[dict] = mapped_column(JSON, default={})      # strategy params
    paper_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String, default="stopped")  # running | stopped | error
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user: Mapped["User"] = relationship("User", back_populates="bots")  # noqa: F821
    trades: Mapped[list["Trade"]] = relationship("Trade", back_populates="bot", cascade="all, delete-orphan")  # noqa: F821
    logs: Mapped[list["BotLog"]] = relationship("BotLog", back_populates="bot", cascade="all, delete-orphan")  # noqa: F821


class BotLog(Base):
    __tablename__ = "bot_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    bot: Mapped["Bot"] = relationship("Bot", back_populates="logs")
