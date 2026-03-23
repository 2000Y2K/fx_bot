from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class AssignmentStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"
    blocked = "blocked"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    teams = relationship("Team", back_populates="project")
    assets = relationship("Asset", back_populates="project")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    project = relationship("Project", back_populates="teams")
    persons = relationship("Person", back_populates="team")


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    whatsapp_number = Column(String(30), unique=True, nullable=True)   
    telegram_id = Column(String(30), unique=True, nullable=True) 
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    team = relationship("Team", back_populates="persons")
    assignments = relationship("Assignment", back_populates="person")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    drive_url = Column(String(500), nullable=True)
    current_version = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="assets")
    assignments = relationship("Assignment", back_populates="asset")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.pending, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    asset = relationship("Asset", back_populates="assignments")
    person = relationship("Person", back_populates="assignments")
    logs = relationship("AssignmentLog", back_populates="assignment")


class AssignmentLog(Base):
    __tablename__ = "assignment_log"

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    changed_by = Column(String(200), nullable=False)  # admin name or "bot"
    old_status = Column(Enum(AssignmentStatus), nullable=True)
    new_status = Column(Enum(AssignmentStatus), nullable=False)
    note = Column(Text, nullable=True)
    changed_at = Column(DateTime, server_default=func.now())

    assignment = relationship("Assignment", back_populates="logs")
