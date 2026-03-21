"""Matches listing and creation."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..auth import verify_admin
from ..database import get_db
from ..models import Match, MatchEvent, Player
from ..schemas import (
    MatchCreate,
    MatchEventNested,
    MatchPublic,
    MessageResponse,
    PlayerOfMatchInfo,
)

router = APIRouter(tags=["matches"])


def _compute_player_of_match(events: list[MatchEvent]) -> PlayerOfMatchInfo | None:
    """Most goals+assists; ties set tied=True (first id wins for display)."""
    tally: dict[int, int] = {}
    for e in events:
        if e.player_id is None:
            continue
        if e.type not in ("goal", "assist"):
            continue
        tally[e.player_id] = tally.get(e.player_id, 0) + 1
    if not tally:
        return None
    best = max(tally.values())
    leaders = sorted([pid for pid, c in tally.items() if c == best])
    return PlayerOfMatchInfo(
        player_id=leaders[0],
        player_name=None,
        contributions=best,
        tied=len(leaders) > 1,
    )


@router.get("/matches", response_model=list[MatchPublic])
def list_matches(db: Session = Depends(get_db)) -> list[MatchPublic]:
    stmt = (
        select(Match)
        .options(joinedload(Match.events).joinedload(MatchEvent.player))
        .order_by(Match.played_on.desc(), Match.id.desc())
    )
    matches = db.scalars(stmt).unique().all()
    out: list[MatchPublic] = []
    for m in matches:
        nested: list[MatchEventNested] = []
        for e in m.events:
            nested.append(
                MatchEventNested(
                    id=e.id,
                    match_id=e.match_id,
                    player_id=e.player_id,
                    player_name=e.player.name if e.player else None,
                    type=e.type,
                    minute=e.minute,
                )
            )
        nested.sort(key=lambda x: x.minute)
        pom = _compute_player_of_match(list(m.events))
        if pom and pom.player_id:
            pl = db.get(Player, pom.player_id)
            pom = PlayerOfMatchInfo(
                player_id=pom.player_id,
                player_name=pl.name if pl else None,
                contributions=pom.contributions,
                tied=pom.tied,
            )
        out.append(
            MatchPublic(
                id=m.id,
                opponent=m.opponent,
                match_date=m.played_on,
                result=m.result,
                goals_for=m.goals_for,
                goals_against=m.goals_against,
                events=nested,
                player_of_match=pom,
            )
        )
    return out


@router.post(
    "/matches",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_match(
    body: MatchCreate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin),
) -> MessageResponse:
    m = Match(
        opponent=body.opponent,
        played_on=body.match_date,
        result=body.result,
        goals_for=body.goals_for,
        goals_against=body.goals_against,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return MessageResponse(message="Match created", id=m.id)
