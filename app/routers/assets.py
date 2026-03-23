from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db.database import get_db
from app.models.models import Asset, Assignment, AssignmentStatus
from app.schemas.schemas import AssetCreate, AssetUpdate, AssetOut, AssignmentOut

router = APIRouter()


@router.post("/", response_model=AssetOut, status_code=201)
def create_asset(data: AssetCreate, db: Session = Depends(get_db)):
    asset = Asset(**data.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/", response_model=list[AssetOut])
def list_assets(project_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Asset)
    if project_id:
        q = q.filter(Asset.project_id == project_id)
    return q.all()


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.patch("/{asset_id}", response_model=AssetOut)
def update_asset(asset_id: int, data: AssetUpdate, db: Session = Depends(get_db)):
    """Admins update drive_url or current_version when a new version is uploaded."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{asset_id}/assignments", response_model=list[AssignmentOut])
def get_asset_assignments(asset_id: int, db: Session = Depends(get_db)):
    """'Who is working on this file?' — main bot query for asset status."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return (
        db.query(Assignment)
        .options(joinedload(Assignment.person), joinedload(Assignment.asset))
        .filter(
            Assignment.asset_id == asset_id,
            Assignment.status.in_([AssignmentStatus.pending, AssignmentStatus.in_progress]),
        )
        .all()
    )
