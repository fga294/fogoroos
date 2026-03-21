"""Pydantic request/response models."""

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


# --- Players ---


class PlayerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    jersey_number: int | None = Field(None, ge=0, le=99)
    position: str | None = Field(None, max_length=64)


class PlayerCreate(PlayerBase):
    pass


class PlayerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    jersey_number: int | None = Field(None, ge=0, le=99)
    position: str | None = Field(None, max_length=64)


class PlayerPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    jersey_number: int | None
    position: str | None
    goals: int = 0
    assists: int = 0
    fitness_score: float | None = None  # latest recorded score


class PlayerDetailPublic(PlayerPublic):
    created_at: datetime


# --- Matches ---


class MatchCreate(BaseModel):
    opponent: str = Field(..., min_length=1, max_length=255)
    match_date: date
    result: str = Field(..., pattern="^(win|loss|draw)$")
    goals_for: int = Field(0, ge=0)
    goals_against: int = Field(0, ge=0)


class MatchEventNested(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    match_id: int
    player_id: int | None
    player_name: str | None = None
    type: str
    minute: int


class PlayerOfMatchInfo(BaseModel):
    """Resolved from contribution counts (goals + assists per player)."""

    player_id: int | None = None
    player_name: str | None = None
    contributions: int = 0
    tied: bool = False


class MatchPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    opponent: str
    match_date: date
    result: str
    goals_for: int
    goals_against: int
    events: list[MatchEventNested] = []
    player_of_match: PlayerOfMatchInfo | None = None


# --- Events ---


class EventCreate(BaseModel):
    match_id: int
    player_id: int | None = None
    type: str = Field(..., pattern="^(goal|assist|conceded_goal)$")
    minute: int = Field(..., ge=0, le=120)


# --- Fitness ---


class FitnessCreate(BaseModel):
    player_id: int
    score: float = Field(..., ge=0, le=10)
    date: date


class FitnessPoint(BaseModel):
    date: date
    score: float


class GoalPoint(BaseModel):
    date: date
    goals: int


class MatchContribution(BaseModel):
    match_id: int
    opponent: str
    match_date: date
    result: str
    goals: int
    assists: int


class PlayerDetailResponse(BaseModel):
    player: PlayerDetailPublic
    goals_over_time: list[GoalPoint]
    fitness_trend: list[FitnessPoint]
    match_contributions: list[MatchContribution]


# --- Stats ---


class TeamSummary(BaseModel):
    total_matches: int
    wins: int
    losses: int
    draws: int
    goals_for: int
    goals_against: int


class LeaderRow(BaseModel):
    player_id: int
    name: str
    jersey_number: int | None
    count: int


class StatsResponse(BaseModel):
    summary: TeamSummary
    top_scorers: list[LeaderRow]
    top_assists: list[LeaderRow]


class MessageResponse(BaseModel):
    message: str
    id: int | None = None
