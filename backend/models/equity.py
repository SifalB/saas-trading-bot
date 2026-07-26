from datetime import datetime, UTC

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class EquitySnapshot(Base):
    """Point-in-time account value for one bot.

    Trades alone cannot produce an equity curve: they show realized P&L at
    irregular moments and say nothing about open positions in between.
    Recording equity on a fixed interval gives a real curve — and therefore a
    real maximum drawdown, which is the number that decides whether a
    strategy is survivable.
    """

    __tablename__ = "equity_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True, nullable=False)

    cash: Mapped[float] = mapped_column(Float, nullable=False)
    deployed: Mapped[float] = mapped_column(Float, nullable=False)
    equity: Mapped[float] = mapped_column(Float, nullable=False)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, default=lambda: datetime.now(UTC)
    )
