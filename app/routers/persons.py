from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.db.database import get_db
from app.models.models import Person, Assignment, AssignmentStatus
from app.schemas.schemas import PersonCreate, PersonUpdate, PersonOut, PersonWithTeam, AssignmentOut, PersonAssignments

router = APIRouter()


@router.post("/", response_model=PersonOut, status_code=201)
def create_person(data: PersonCreate, db: Session = Depends(get_db)):
    person = Person(**data.model_dump())
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.get("/", response_model=list[PersonOut])
def list_persons(team_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Person)
    if team_id:
        q = q.filter(Person.team_id == team_id)
    return q.all()


@router.patch("/{person_id}", response_model=PersonOut)
def update_person(person_id: int, data: PersonUpdate, db: Session = Depends(get_db)):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(person, field, value)
    db.commit()
    db.refresh(person)
    return person


@router.get("/by-whatsapp/{number}", response_model=PersonWithTeam)
def get_by_whatsapp(number: str, db: Session = Depends(get_db)):
    person = (
        db.query(Person)
        .options(joinedload(Person.team))
        .filter(Person.whatsapp_number == number)
        .first()
    )
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.get("/by-telegram/{telegram_id}", response_model=PersonWithTeam)
def get_by_telegram(telegram_id: str, db: Session = Depends(get_db)):
    person = (
        db.query(Person)
        .options(joinedload(Person.team))
        .filter(Person.telegram_id == telegram_id)
        .first()
    )
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.get("/{person_id}/assignments", response_model=PersonAssignments)
def get_person_assignments(
    person_id: int,
    include_done: bool = Query(False, description="Include done assignments"),
    db: Session = Depends(get_db),
):
    person = (
        db.query(Person)
        .options(joinedload(Person.team))
        .filter(Person.id == person_id)
        .first()
    )
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    q = db.query(Assignment).options(
        joinedload(Assignment.asset), joinedload(Assignment.person)
    ).filter(Assignment.person_id == person_id)

    if not include_done:
        # Bot only sees active ones
        q = q.filter(Assignment.status.in_([AssignmentStatus.pending, AssignmentStatus.in_progress]))
    else:
        # Admin sees everything except blocked (or all if needed)
        pass

    assignments = q.order_by(Assignment.updated_at.desc()).all()
    return {"person": person, "assignments": assignments}