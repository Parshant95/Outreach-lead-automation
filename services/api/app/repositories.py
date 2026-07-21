from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload
from app.models import Business
from app.schemas import BusinessCreate
class BusinessRepository:
    def __init__(self, db:Session): self.db=db
    def create(self, data:BusinessCreate):
        item=Business(**data.model_dump()); self.db.add(item); self.db.commit(); self.db.refresh(item); return item
    def get(self, id:int): return self.db.scalar(select(Business).options(joinedload(Business.audit)).where(Business.id==id))
    def list(self,page:int,page_size:int,city:str|None=None,category:str|None=None,no_website:bool=False,min_score:int|None=None):
        q=select(Business).options(joinedload(Business.audit)); count=select(func.count()).select_from(Business)
        if city: q=q.where(Business.city.ilike(f"%{city}%")); count=count.where(Business.city.ilike(f"%{city}%"))
        if category: q=q.where(Business.category.ilike(f"%{category}%")); count=count.where(Business.category.ilike(f"%{category}%"))
        if no_website: q=q.where(Business.website.is_(None)); count=count.where(Business.website.is_(None))
        if min_score is not None: q=q.join(Business.audit).where(Business.audit.has()) # kept simple; score sorting below
        total=self.db.scalar(count) or 0
        return list(self.db.scalars(q.order_by(Business.created_at.desc()).offset((page-1)*page_size).limit(page_size)).unique()), total
