from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.config import get_db
from app.models.models import History, Recipe

router = APIRouter()


@router.get('/history')
def list_history(limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(History).order_by(History.created_at.desc()).limit(limit).all()
    out = []
    for h in q:
        recipe_name = None
        if h.recipe_id:
            r = db.query(Recipe).filter(Recipe.id == h.recipe_id).first()
            recipe_name = r.name if r else None
        out.append({
            'id': h.id,
            'user_id': h.user_id,
            'recipe_id': h.recipe_id,
            'recipe_name': recipe_name,
            'cup_id': h.cup_id,
            'ml_total': h.ml_total,
            'mode': h.mode,
            'xp_gained': h.xp_gained,
            'success': h.success,
            'created_at': h.created_at.isoformat()
        })
    return out
