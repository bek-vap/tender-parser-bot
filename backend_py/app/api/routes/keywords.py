from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from app.db.deps import get_db
from app.models.tender import Keyword

router = APIRouter(prefix="/keywords", tags=["keywords"])


class KeywordCreate(BaseModel):
    phrase: str
    is_active: bool = True


class KeywordUpdate(BaseModel):
    phrase: str | None = None
    is_active: bool | None = None


class KeywordResponse(BaseModel):
    id: str
    phrase: str
    is_active: bool

    class Config:
        from_attributes = True


@router.get("", response_model=List[KeywordResponse])
def list_keywords(
    active_only: bool = False,
    db: Session = Depends(get_db)
) -> List[Keyword]:
    query = db.query(Keyword)
    if active_only:
        query = query.filter(Keyword.is_active == True)
    items = query.order_by(Keyword.phrase.asc()).all()
    return items


@router.get("/{keyword_id}", response_model=KeywordResponse)
def get_keyword(keyword_id: str, db: Session = Depends(get_db)) -> Keyword:
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword


@router.post("", response_model=KeywordResponse)
def create_keyword(keyword_data: KeywordCreate, db: Session = Depends(get_db)) -> Keyword:
    # Check if keyword already exists
    existing = db.query(Keyword).filter(Keyword.phrase == keyword_data.phrase.strip().lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Keyword with this phrase already exists")
    
    keyword = Keyword(
        phrase=keyword_data.phrase.strip(),
        is_active=keyword_data.is_active
    )
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.put("/{keyword_id}", response_model=KeywordResponse)
def update_keyword(
    keyword_id: str, 
    keyword_data: KeywordUpdate, 
    db: Session = Depends(get_db)
) -> Keyword:
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    # Check for duplicate phrase if updating phrase
    if keyword_data.phrase and keyword_data.phrase.strip().lower() != keyword.phrase.lower():
        existing = db.query(Keyword).filter(
            Keyword.phrase == keyword_data.phrase.strip().lower(),
            Keyword.id != keyword_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Keyword with this phrase already exists")
        keyword.phrase = keyword_data.phrase.strip()
    
    if keyword_data.is_active is not None:
        keyword.is_active = keyword_data.is_active
    
    db.commit()
    db.refresh(keyword)
    return keyword


@router.delete("/{keyword_id}")
def delete_keyword(keyword_id: str, db: Session = Depends(get_db)) -> dict:
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    db.delete(keyword)
    db.commit()
    return {"message": "Keyword deleted successfully"}


@router.post("/batch", response_model=List[KeywordResponse])
def create_keywords_batch(keywords_data: List[KeywordCreate], db: Session = Depends(get_db)) -> List[Keyword]:
    created_keywords = []
    errors = []
    
    for i, keyword_data in enumerate(keywords_data):
        try:
            # Check if keyword already exists
            existing = db.query(Keyword).filter(Keyword.phrase == keyword_data.phrase.strip().lower()).first()
            if existing:
                errors.append(f"Row {i+1}: Keyword '{keyword_data.phrase}' already exists")
                continue
            
            keyword = Keyword(
                phrase=keyword_data.phrase.strip(),
                is_active=keyword_data.is_active
            )
            db.add(keyword)
            created_keywords.append(keyword)
            
        except Exception as e:
            errors.append(f"Row {i+1}: {str(e)}")
    
    if created_keywords:
        db.commit()
        for keyword in created_keywords:
            db.refresh(keyword)
    
    if errors:
        raise HTTPException(
            status_code=400, 
            detail=f"Some keywords failed to create: {'; '.join(errors)}"
        )
    
    return created_keywords


@router.get("/stats/summary")
def get_keywords_stats(db: Session = Depends(get_db)) -> dict:
    total = db.query(Keyword).count()
    active = db.query(Keyword).filter(Keyword.is_active == True).count()
    inactive = total - active
    
    return {
        "total": total,
        "active": active,
        "inactive": inactive
    }
