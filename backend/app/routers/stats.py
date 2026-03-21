"""Aggregated read-only stats for dashboard."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Match, MatchEvent, Player
from ..schemas import LeaderRow, StatsResponse, TeamSummary

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    matches = db.scalars(select(Match)).all()
    total = len(matches)
    wins = sum(1 for m in matches if m.result == "win")
    losses = sum(1 for m in matches if m.result == "loss")
    draws = sum(1 for m in matches if m.result == "draw")
    gf = sum(m.goals_for for m in matches)
    ga = sum(m.goals_against for m in matches)

    goal_cnt = func.count().label("goal_cnt")
    goal_rows = db.execute(
        select(MatchEvent.player_id, goal_cnt, Player.name, Player.jersey_number)
        .join(Player, Player.id == MatchEvent.player_id)
        .where(MatchEvent.type == "goal", MatchEvent.player_id.isnot(None))
        .group_by(MatchEvent.player_id, Player.name, Player.jersey_number)
        .order_by(goal_cnt.desc(), Player.name)
    ).all()
    top_scorers = [
        LeaderRow(player_id=int(r[0]), name=str(r[2]), jersey_number=r[3], count=int(r[1])) for r in goal_rows
    ]

    ast_cnt = func.count().label("ast_cnt")
    ast_rows = db.execute(
        select(MatchEvent.player_id, ast_cnt, Player.name, Player.jersey_number)
        .join(Player, Player.id == MatchEvent.player_id)
        .where(MatchEvent.type == "assist", MatchEvent.player_id.isnot(None))
        .group_by(MatchEvent.player_id, Player.name, Player.jersey_number)
        .order_by(ast_cnt.desc(), Player.name)
    ).all()
    top_assists = [
        LeaderRow(player_id=int(r[0]), name=str(r[2]), jersey_number=r[3], count=int(r[1])) for r in ast_rows
    ]

    return StatsResponse(
        summary=TeamSummary(
            total_matches=total,
            wins=wins,
            losses=losses,
            draws=draws,
            goals_for=gf,
            goals_against=ga,
        ),
        top_scorers=top_scorers,
        top_assists=top_assists,
    )
