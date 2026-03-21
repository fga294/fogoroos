"""Fitness score entry."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import verify_admin
from ..database import get_db
from ..models import FitnessScore, Player
from ..schemas import FitnessCreate, MessageResponse

router = APIRouter(tags=["fitness"])


@router.post("/fitness", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_fitness(
    body: FitnessCreate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin),
) -> MessageResponse:
    pl = db.get(Player, body.player_id)
    if not pl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    row = FitnessScore(player_id=body.player_id, score=Decimal(str(body.score)), recorded_on=body.date)
    db.add(row)
    db.commit()
    db.refresh(row)
    return MessageResponse(message="Fitness score saved", id=row.id)
