from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from app.database import get_db
from app import models, schemas
from app.dependencies.permission import permission_required

router = APIRouter(
    prefix="/api/stores",
    tags=["Reviews"]
)


@router.post("/{store_id}/reviews", response_model=schemas.ReviewResponse)
def create_review(
    store_id: str,
    review: schemas.ReviewCreate,
    db: Session = Depends(get_db)
):
    store = db.query(models.Store).filter(
        models.Store.store_id == store_id
    ).first()

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    new_review = models.Review(
        review_id=str(uuid.uuid4()),
        store_id=store_id,
        rating=review.rating,
        comment=review.comment,
        flagged=False
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return new_review


@router.get("/{store_id}/reviews", response_model=list[schemas.ReviewResponse])
def get_reviews(
    store_id: str,
    db: Session = Depends(get_db)
):
    store = db.query(models.Store).filter(
        models.Store.store_id == store_id
    ).first()

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    reviews = db.query(models.Review).filter(
        models.Review.store_id == store_id,
        models.Review.flagged == False
    ).all()

    return reviews


@router.get("/{store_id}/rating", response_model=schemas.RatingSummary)
def get_rating_summary(
    store_id: str,
    db: Session = Depends(get_db)
):
    store = db.query(models.Store).filter(
        models.Store.store_id == store_id
    ).first()

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    result = db.query(
        func.avg(models.Review.rating),
        func.count(models.Review.review_id)
    ).filter(
        models.Review.store_id == store_id,
        models.Review.flagged == False
    ).first()

    average_rating = result[0] or 0
    review_count = result[1] or 0

    return {
        "store_id": store_id,
        "average_rating": round(float(average_rating), 2),
        "review_count": review_count
    }
    
    
    
@router.patch("/reviews/{review_id}/flag", response_model=schemas.ReviewResponse)
def flag_review(
    review_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("manage_users"))
):
    review = db.query(models.Review).filter(
        models.Review.review_id == review_id
    ).first()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    review.flagged = True

    db.commit()
    db.refresh(review)

    return review


