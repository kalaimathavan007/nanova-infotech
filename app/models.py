from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="user") # "admin" or "user"
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="users")
    attendances = relationship("Attendance", back_populates="submitted_by_user")

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    idea_title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    domain = Column(String, nullable=True) # e.g. EdTech, HealthTech, AI, AgriTech
    status = Column(String, default="Incubated") # "Incubated", "Graduated", "Pre-Incubation"
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="team")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="team", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="team", cascade="all, delete-orphan")

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    role_in_team = Column(String, default="Member") # Developer, Lead, UI/UX, Pitcher, etc.
    phone = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="members")

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    date = Column(String, nullable=False) # YYYY-MM-DD
    status = Column(String, nullable=False) # "Present", "Absent", "Half Day", "Working Remotely"
    work_summary = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="attendances")
    submitted_by_user = relationship("User", back_populates="attendances")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    sender_name = Column(String, nullable=False)
    sender_role = Column(String, nullable=False) # "admin" or "user"
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="messages")

class AdminSetting(Base):
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True, index=True)
    incubation_name = Column(String, default="Nanova Infotech")
    allowed_admin_emails = Column(Text, default="kalaimathavan007@gmail.com, admin@nanovainfotech.com")
    announcement = Column(Text, default="Welcome to the Nanova Infotech Portal! Please submit your daily attendance regularly.")
    updated_at = Column(DateTime, default=datetime.utcnow)
