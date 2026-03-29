from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Team
from app.schemas.schemas import TeamCreate, TeamOut

router = APIRouter()


@router.post("", response_model=TeamOut, status_code=201)
def create_team(data: TeamCreate, db: Session = Depends(get_db)):
    team = Team(**data.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("", response_model=list[TeamOut])
def list_teams(project_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Team)
    if project_id:
        q = q.filter(Team.project_id == project_id)
    return q.all()


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team
