"""ORM models — mirrors scripts/init_schema.sql."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    pass


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    jersey_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    events: Mapped[list["MatchEvent"]] = relationship("MatchEvent", back_populates="player")
    fitness_scores: Mapped[list["FitnessScore"]] = relationship("FitnessScore", back_populates="player")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    opponent: Mapped[str] = mapped_column(String(255), nullable=False)
    played_on: Mapped[date] = mapped_column("match_date", Date, nullable=False)
    result: Mapped[str] = mapped_column(Enum("win", "loss", "draw", name="match_result"), nullable=False)
    goals_for: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    goals_against: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    events: Mapped[list["MatchEvent"]] = relationship("MatchEvent", back_populates="match")


class MatchEvent(Base):
    """Per-match timeline: goals, assists, or conceded goals."""

    __tablename__ = "match_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[str] = mapped_column(
        Enum("goal", "assist", "conceded_goal", name="event_type"),
        nullable=False,
    )
    minute: Mapped[int] = mapped_column(Integer, nullable=False)

    match: Mapped["Match"] = relationship("Match", back_populates="events")
    player: Mapped["Player | None"] = relationship("Player", back_populates="events")


class FitnessScore(Base):
    __tablename__ = "fitness_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False)
    recorded_on: Mapped[date] = mapped_column("score_date", Date, nullable=False)

    player: Mapped["Player"] = relationship("Player", back_populates="fitness_scores")
