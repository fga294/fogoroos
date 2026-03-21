"""Player CRUD and read-only detail."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from ..auth import verify_admin
from ..database import get_db
from ..models import FitnessScore, Match, MatchEvent, Player
from ..schemas import (
    GoalPoint,
    MatchContribution,
    FitnessPoint,
    MessageResponse,
    PlayerCreate,
    PlayerDetailPublic,
    PlayerDetailResponse,
    PlayerPublic,
    PlayerUpdate,
)

router = APIRouter(tags=["players"])


def _goal_assist_counts(db: Session) -> tuple[dict[int, int], dict[int, int]]:
    goals_rows = db.execute(
        select(MatchEvent.player_id, func.count())
        .where(MatchEvent.type == "goal", MatchEvent.player_id.isnot(None))
        .group_by(MatchEvent.player_id)
    ).all()
    assists_rows = db.execute(
        select(MatchEvent.player_id, func.count())
        .where(MatchEvent.type == "assist", MatchEvent.player_id.isnot(None))
        .group_by(MatchEvent.player_id)
    ).all()
    return {int(r[0]): int(r[1]) for r in goals_rows if r[0]}, {
        int(r[0]): int(r[1]) for r in assists_rows if r[0]
    }


def _latest_fitness_map(db: Session) -> dict[int, float]:
    """Latest fitness score per player by most recent score_date."""
    mx = func.max(FitnessScore.recorded_on).label("md")
    sub = (
        select(FitnessScore.player_id, mx)
        .group_by(FitnessScore.player_id)
        .subquery()
    )
    fs = aliased(FitnessScore)
    rows = db.execute(
        select(fs.player_id, fs.score).join(
            sub,
            (fs.player_id == sub.c.player_id) & (fs.recorded_on == sub.c.md),
        )
    ).all()
    return {int(r[0]): float(r[1]) for r in rows}


@router.get("/players", response_model=list[PlayerPublic])
def list_players(db: Session = Depends(get_db)) -> list[PlayerPublic]:
    goals_m, ast_m = _goal_assist_counts(db)
    fit_m = _latest_fitness_map(db)
    players = db.scalars(select(Player).order_by(Player.name)).all()
    return [
        PlayerPublic(
            id=p.id,
            name=p.name,
            jersey_number=p.jersey_number,
            position=p.position,
            goals=goals_m.get(p.id, 0),
            assists=ast_m.get(p.id, 0),
            fitness_score=fit_m.get(p.id),
        )
        for p in players
    ]


@router.get("/player/{player_id}", response_model=PlayerDetailResponse)
def get_player_detail(
    player_id: int,
    db: Session = Depends(get_db),
) -> PlayerDetailResponse:
    p = db.get(Player, player_id)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )

    goals_m, ast_m = _goal_assist_counts(db)
    fit_m = _latest_fitness_map(db)

    base = PlayerDetailPublic(
        id=p.id,
        name=p.name,
        jersey_number=p.jersey_number,
        position=p.position,
        created_at=p.created_at,
        goals=goals_m.get(p.id, 0),
        assists=ast_m.get(p.id, 0),
        fitness_score=fit_m.get(p.id),
    )

    # Goals per match date (timeline of scoring games)
    g_rows = db.execute(
        select(Match.played_on, func.count())
        .join(MatchEvent, MatchEvent.match_id == Match.id)
        .where(MatchEvent.player_id == player_id, MatchEvent.type == "goal")
        .group_by(Match.played_on)
        .order_by(Match.played_on)
    ).all()
    goals_over_time = [GoalPoint(date=r[0], goals=int(r[1])) for r in g_rows]

    f_rows = db.scalars(
        select(FitnessScore)
        .where(FitnessScore.player_id == player_id)
        .order_by(FitnessScore.recorded_on, FitnessScore.id)
    ).all()
    fitness_trend = [
        FitnessPoint(date=x.recorded_on, score=float(x.score)) for x in f_rows
    ]

    # Per-match goal/assist counts for this player
    mc_rows = db.execute(
        select(Match.id, Match.opponent, Match.played_on, Match.result)
        .join(MatchEvent, MatchEvent.match_id == Match.id)
        .where(MatchEvent.player_id == player_id)
        .distinct()
        .order_by(Match.played_on.desc())
    ).all()
    contributions: list[MatchContribution] = []
    for mid, opp, mdate, res in mc_rows:
        gc = db.scalar(
            select(func.count())
            .select_from(MatchEvent)
            .where(
                MatchEvent.match_id == mid,
                MatchEvent.player_id == player_id,
                MatchEvent.type == "goal",
            )
        )
        ac = db.scalar(
            select(func.count())
            .select_from(MatchEvent)
            .where(
                MatchEvent.match_id == mid,
                MatchEvent.player_id == player_id,
                MatchEvent.type == "assist",
            )
        )
        contributions.append(
            MatchContribution(
                match_id=int(mid),
                opponent=str(opp),
                match_date=mdate,
                result=str(res),
                goals=int(gc or 0),
                assists=int(ac or 0),
            )
        )

    return PlayerDetailResponse(
        player=base,
        goals_over_time=goals_over_time,
        fitness_trend=fitness_trend,
        match_contributions=contributions,
    )


@router.post(
    "/players",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_player(
    body: PlayerCreate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin),
) -> MessageResponse:
    p = Player(
        name=body.name,
        jersey_number=body.jersey_number,
        position=body.position,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return MessageResponse(message="Player created", id=p.id)


@router.put("/players/{player_id}", response_model=MessageResponse)
def update_player(
    player_id: int,
    body: PlayerUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin),
) -> MessageResponse:
    p = db.get(Player, player_id)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )
    for k, v in data.items():
        setattr(p, k, v)
    db.commit()
    return MessageResponse(message="Player updated", id=p.id)


@router.delete("/players/{player_id}", response_model=MessageResponse)
def delete_player(
    player_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin),
) -> MessageResponse:
    p = db.get(Player, player_id)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    db.delete(p)
    db.commit()
    return MessageResponse(message="Player deleted", id=player_id)
