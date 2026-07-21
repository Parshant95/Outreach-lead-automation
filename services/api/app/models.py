import enum
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class LeadStatus(str, enum.Enum): NEW="New"; CONTACTED="Contacted"; INTERESTED="Interested"; MEETING="Meeting Scheduled"; PROPOSAL="Proposal Sent"; WON="Won"; LOST="Lost"
class Role(str, enum.Enum): ADMIN="admin"; SALES="sales"; MANAGER="manager"
class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True); email: Mapped[str]=mapped_column(String(255), unique=True); password_hash: Mapped[str]=mapped_column(String(255)); role: Mapped[Role]=mapped_column(default=Role.SALES)
class Business(Base):
    __tablename__="businesses"
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(255), index=True); category: Mapped[str|None]=mapped_column(String(100), index=True); city: Mapped[str|None]=mapped_column(String(100), index=True); country: Mapped[str|None]=mapped_column(String(100)); address: Mapped[str|None]=mapped_column(Text); phone: Mapped[str|None]=mapped_column(String(60)); email: Mapped[str|None]=mapped_column(String(255)); website: Mapped[str|None]=mapped_column(String(500)); maps_url: Mapped[str|None]=mapped_column(String(500)); latitude: Mapped[float|None]=mapped_column(Float); longitude: Mapped[float|None]=mapped_column(Float); rating: Mapped[float|None]=mapped_column(Float); review_count: Mapped[int]=mapped_column(default=0); status: Mapped[LeadStatus]=mapped_column(default=LeadStatus.NEW); created_at: Mapped[datetime]=mapped_column(default=datetime.utcnow)
    audit: Mapped["Audit|None"]=relationship(back_populates="business", uselist=False, cascade="all, delete-orphan")
class Audit(Base):
    __tablename__="audits"
    id: Mapped[int]=mapped_column(primary_key=True); business_id: Mapped[int]=mapped_column(ForeignKey("businesses.id"), unique=True); score: Mapped[int]=mapped_column(default=0); priority: Mapped[str]=mapped_column(String(20), default="Low"); lead_type: Mapped[str]=mapped_column(String(80)); website_score: Mapped[int]=mapped_column(default=0); seo_score: Mapped[int]=mapped_column(default=0); performance_score: Mapped[int]=mapped_column(default=0); issues: Mapped[list]=mapped_column(JSON, default=list); findings: Mapped[dict]=mapped_column(JSON, default=dict); screenshot_url: Mapped[str|None]=mapped_column(String(500)); analyzed_at: Mapped[datetime]=mapped_column(default=datetime.utcnow)
    business: Mapped[Business]=relationship(back_populates="audit")
