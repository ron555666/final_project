from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from geopy.distance import geodesic
from datetime import datetime
from io import StringIO
import math
import csv

from app.database import get_db
from app import models, schemas
from app.utils.geocoding import geocode_location
from app.dependencies.permission import permission_required
from app.rate_limit import limiter


router = APIRouter(
    prefix="/api/stores",
    tags=["Stores"]
)


def is_store_open_now(store):
    now = datetime.now()
    weekday = now.strftime("%a").lower()

    hours_field = f"hours_{weekday}"
    hours = getattr(store, hours_field)

    if not hours:
        return False

    hours = hours.strip().lower()

    if hours == "closed":
        return False

    try:
        open_time, close_time = hours.split("-")
        open_time = open_time.strip()
        close_time = close_time.strip()
        current_time = now.strftime("%H:%M")

        return open_time <= current_time <= close_time
    except Exception:
        return False


@router.post("/", response_model=schemas.StoreResponse)
def create_store(
    store: schemas.StoreCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("create_store"))
):
    existing_store = db.query(models.Store).filter(
        models.Store.store_id == store.store_id
    ).first()

    if existing_store:
        raise HTTPException(status_code=400, detail="Store already exists")

    new_store = models.Store(**store.model_dump())

    db.add(new_store)
    db.commit()
    db.refresh(new_store)

    return new_store


@router.get("/", response_model=list[schemas.StoreResponse])
def get_stores(db: Session = Depends(get_db)):
    return db.query(models.Store).all()


@router.get("/{store_id}", response_model=schemas.StoreResponse)
def get_store(
    store_id: str,
    db: Session = Depends(get_db)
):
    store = db.query(models.Store).filter(
        models.Store.store_id == store_id
    ).first()

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    return store


@router.patch("/{store_id}", response_model=schemas.StoreResponse)
def update_store(
    store_id: str,
    store_update: schemas.StoreUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("update_store"))
):
    store = db.query(models.Store).filter(
        models.Store.store_id == store_id
    ).first()

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    update_data = store_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(store, key, value)

    db.commit()
    db.refresh(store)

    return store


@router.delete("/{store_id}")
def delete_store(
    store_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("delete_store"))
):
    store = db.query(models.Store).filter(
        models.Store.store_id == store_id
    ).first()

    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    store.status = "inactive"

    db.commit()
    db.refresh(store)

    return {
        "message": "Store deactivated successfully",
        "store_id": store.store_id,
        "status": store.status
    }


@router.post("/search", response_model=list[schemas.StoreSearchResult])
@limiter.limit("10/minute")
@limiter.limit("100/hour")
def search_stores(
    request: Request,
    search: schemas.StoreSearchRequest,
    db: Session = Depends(get_db)
):
    radius = search.radius_miles

    if radius > 100:
        raise HTTPException(status_code=400, detail="radius_miles cannot exceed 100")

    if search.latitude is not None and search.longitude is not None:
        lat = search.latitude
        lon = search.longitude

    elif search.address:
        location = geocode_location(search.address)

        if not location:
            raise HTTPException(status_code=400, detail="Address could not be geocoded")

        lat = location["latitude"]
        lon = location["longitude"]

    elif search.postal_code:
        zip_query = f"{search.postal_code}, USA"
        location = geocode_location(zip_query)

        if not location:
            raise HTTPException(status_code=400, detail="Postal code could not be geocoded")

        lat = location["latitude"]
        lon = location["longitude"]

    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either latitude/longitude, address, or postal_code"
        )

    latitude_delta = radius / 69.0
    longitude_delta = radius / (69.0 * math.cos(math.radians(lat)))

    min_lat = lat - latitude_delta
    max_lat = lat + latitude_delta
    min_lon = lon - longitude_delta
    max_lon = lon + longitude_delta

    query = db.query(models.Store).filter(
        models.Store.status == "active",
        models.Store.latitude.between(min_lat, max_lat),
        models.Store.longitude.between(min_lon, max_lon)
    )

    if search.store_types:
        query = query.filter(models.Store.store_type.in_(search.store_types))

    if search.services:
        for service in search.services:
            query = query.filter(models.Store.services.ilike(f"%{service}%"))

    candidate_stores = query.all()
    results = []

    for store in candidate_stores:
        open_status = is_store_open_now(store)

        if search.open_now is True and not open_status:
            continue

        distance = geodesic(
            (lat, lon),
            (store.latitude, store.longitude)
        ).miles

        if distance > radius:
            continue

        rating_result = db.query(
            func.avg(models.Review.rating),
            func.count(models.Review.review_id)
        ).filter(
            models.Review.store_id == store.store_id,
            models.Review.flagged == False
        ).first()

        average_rating = rating_result[0] or 0
        review_count = rating_result[1] or 0

        if search.min_rating is not None and average_rating < search.min_rating:
            continue

        store_data = schemas.StoreResponse.model_validate(store).model_dump()
        store_data["distance_miles"] = round(distance, 2)
        store_data["is_open_now"] = open_status
        store_data["average_rating"] = round(float(average_rating), 2)
        store_data["review_count"] = review_count

        results.append(store_data)

    results.sort(key=lambda x: x["distance_miles"])

    return results


@router.post("/import", response_model=schemas.ImportReport)
def import_stores(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("import_store"))
):
    content = file.file.read().decode("utf-8")
    csv_reader = csv.DictReader(StringIO(content))

    created = 0
    updated = 0
    failed = 0

    for row in csv_reader:
        try:
            existing = db.query(models.Store).filter(
                models.Store.store_id == row["store_id"]
            ).first()

            if existing:
                for key, value in row.items():
                    if hasattr(existing, key) and value:
                        setattr(existing, key, value)

                updated += 1

            else:
                new_store = models.Store(**row)
                db.add(new_store)
                created += 1

        except Exception:
            failed += 1

    db.commit()

    return {
        "created": created,
        "updated": updated,
        "failed": failed
    }


@router.get("/export/csv")
def export_stores_csv(
    db: Session = Depends(get_db)
):
    stores = db.query(models.Store).all()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "store_id",
        "name",
        "store_type",
        "status",
        "latitude",
        "longitude",
        "address_city",
        "address_state",
        "address_postal_code",
        "services"
    ])

    for store in stores:
        writer.writerow([
            store.store_id,
            store.name,
            store.store_type,
            store.status,
            store.latitude,
            store.longitude,
            store.address_city,
            store.address_state,
            store.address_postal_code,
            store.services
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=stores_export.csv"
        }
    )