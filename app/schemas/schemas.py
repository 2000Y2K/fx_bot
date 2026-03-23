from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.models import AssignmentStatus


# --- Project ---
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectOut(ProjectCreate):
    id: int
    created_at: datetime
    class Config: from_attributes = True


# --- Team ---
class TeamCreate(BaseModel):
    name: str
    project_id: int

class TeamOut(TeamCreate):
    id: int
    class Config: from_attributes = True


# --- Person ---
class PersonCreate(BaseModel):
    name: str
    whatsapp_number: Optional[str] = None
    telegram_id: Optional[str] = None
    team_id: int

class PersonUpdate(BaseModel):
    name: Optional[str] = None
    whatsapp_number: Optional[str] = None
    telegram_id: Optional[str] = None
    team_id: Optional[int] = None

class PersonOut(BaseModel):
    id: int
    name: str
    whatsapp_number: Optional[str] = None
    telegram_id: Optional[str] = None
    team_id: int
    class Config: from_attributes = True

class PersonWithTeam(BaseModel):
    id: int
    name: str
    whatsapp_number: Optional[str] = None
    telegram_id: Optional[str] = None
    team: TeamOut
    class Config: from_attributes = True


# --- Asset ---
class AssetCreate(BaseModel):
    name: str
    project_id: int
    drive_url: Optional[str] = None
    current_version: Optional[str] = None
    notes: Optional[str] = None

class AssetUpdate(BaseModel):
    drive_url: Optional[str] = None
    current_version: Optional[str] = None
    notes: Optional[str] = None

class AssetOut(AssetCreate):
    id: int
    updated_at: datetime
    class Config: from_attributes = True


# --- Assignment ---
class AssignmentCreate(BaseModel):
    asset_id: int
    person_id: int
    notes: Optional[str] = None
    created_by: str

class AssignmentStatusUpdate(BaseModel):
    status: AssignmentStatus
    changed_by: str
    note: Optional[str] = None

class AssignmentOut(BaseModel):
    id: int
    asset: AssetOut
    person: PersonOut
    status: AssignmentStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


# --- Bot / Admin queries ---
class PersonAssignments(BaseModel):
    person: PersonWithTeam
    assignments: list[AssignmentOut]

class TeamAssignments(BaseModel):
    team: TeamOut
    assignments: list[AssignmentOut]