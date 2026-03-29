from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db.database import get_db
from app.models.models import Assignment, AssignmentLog, AssignmentStatus, Person, Team
from app.schemas.schemas import AssignmentCreate, AssignmentOut, AssignmentStatusUpdate, TeamAssignments

router = APIRouter()


@router.post("", response_model=AssignmentOut, status_code=201)
def create_assignment(data: AssignmentCreate, db: Session = Depends(get_db)):
    """Admins create assignments."""
    assignment = Assignment(
        asset_id=data.asset_id,
        person_id=data.person_id,
        notes=data.notes,
        status=AssignmentStatus.pending,
    )
    db.add(assignment)
    db.flush()  # get the id before commit

    log = AssignmentLog(
        assignment_id=assignment.id,
        changed_by=data.created_by,
        old_status=None,
        new_status=AssignmentStatus.pending,
        note="Assignment created",
    )
    db.add(log)
    db.commit()
    db.refresh(assignment)
    return _load_full(assignment.id, db)


@router.patch("/{assignment_id}/status", response_model=AssignmentOut)
def update_status(assignment_id: int, data: AssignmentStatusUpdate, db: Session = Depends(get_db)):
    """Workers or admins update the status of an assignment."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    log = AssignmentLog(
        assignment_id=assignment.id,
        changed_by=data.changed_by,
        old_status=assignment.status,
        new_status=data.status,
        note=data.note,
    )
    db.add(log)
    assignment.status = data.status
    db.commit()
    return _load_full(assignment.id, db)


@router.get("/team/{team_id}", response_model=TeamAssignments)
def get_team_assignments(team_id: int, db: Session = Depends(get_db)):
    """'What does my team have?' — main bot query for team view."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    person_ids = [p.id for p in db.query(Person).filter(Person.team_id == team_id).all()]

    assignments = (
        db.query(Assignment)
        .options(joinedload(Assignment.asset), joinedload(Assignment.person))
        .filter(
            Assignment.person_id.in_(person_ids),
            Assignment.status.in_([AssignmentStatus.pending, AssignmentStatus.in_progress]),
        )
        .all()
    )
    return {"team": team, "assignments": assignments}


@router.get("/{assignment_id}/log")
def get_assignment_log(assignment_id: int, db: Session = Depends(get_db)):
    """Full history of status changes for an assignment."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment.logs


def _load_full(assignment_id: int, db: Session) -> Assignment:
    return (
        db.query(Assignment)
        .options(joinedload(Assignment.asset), joinedload(Assignment.person))
        .filter(Assignment.id == assignment_id)
        .first()
    )
