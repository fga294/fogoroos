"""Match event creation (goals, assists, conceded)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import verify_admin
from ..database import get_db
from ..models import Match, MatchEvent, Player
from ..schemas import EventCreate, MessageResponse

router = APIRouter(tags=["events"])


@router.post("/events", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    body: EventCreate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin),
) -> MessageResponse:
    if body.type in ("goal", "assist") and body.player_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="player_id is required for goal and assist events",
        )

    player_id = None if body.type == "conceded_goal" else body.player_id

    m = db.get(Match, body.match_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if player_id is not None:
        pl = db.get(Player, player_id)
        if not pl:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    ev = MatchEvent(
        match_id=body.match_id,
        player_id=player_id,
        type=body.type,
        minute=body.minute,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return MessageResponse(message="Event recorded", id=ev.id)
