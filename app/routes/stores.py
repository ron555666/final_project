from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from geopy.distance import geodesic
from datetime import datetime
from io import StringIO
import math
import csv
import uuid

from app.database import get_db
from app import models, schemas
from app.utils.geocoding import geocode_location
from app.dependencies.permission import permission_required
from app.rate_limit import limiter


router = APIRouter(
    prefix="/api/admin/stores",
    tags=["Admin Stores"]
)

public_router = APIRouter(
    prefix="/api/stores",
    tags=["Public Store Search"]
)

def is_store_open_now(store):
    """
    Check if the store is open at current time.
    Return True if open, otherwise False.
    """
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
    
def get_or_create_services(service_names, db):
    service_items = []

    if not service_names:
        return service_items

    for service_name in service_names:
        clean_name = service_name.strip()

        if not clean_name:
            continue

        service = db.query(models.Service).filter(
            models.Service.name == clean_name
        ).first()

        if not service:
            service = models.Service(
                service_id=str(uuid.uuid4()),
                name=clean_name
            )
            db.add(service)
            db.flush()

        service_items.append(service)

    return service_items

@router.post("/", response_model=schemas.StoreResponse)
def create_store(
    store: schemas.StoreCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("create_store"))
):
    """
    Create a new store.
    Check if store_id already exists.
    Requires permission: create_store.
    """
    existing_store = db.query(models.Store).filter(
        models.Store.store_id == store.store_id
    ).first()

    if existing_store:
        raise HTTPException(status_code=400, detail="Store already exists")

    store_data = store.model_dump()
    service_names = store_data.pop("services", None)

    if store_data.get("latitude") is None or store_data.get("longitude") is None:
        full_address = (
            f"{store.address_street}, {store.address_city}, "
            f"{store.address_state} {store.address_postal_code}, "
            f"{store.address_country}"
        )

        location = geocode_location(full_address)

        if not location:
            raise HTTPException(
                status_code=400,
                detail="Address could not be geocoded"
            )

        store_data["latitude"] = location["latitude"]
        store_data["longitude"] = location["longitude"]

    new_store = models.Store(**store_data)
    
    new_store.service_items = get_or_create_services(service_names, db)
    new_store.services = "|".join(service_names) if service_names else None

    db.add(new_store)
    db.commit()
    db.refresh(new_store)

    return new_store


@router.get("/", response_model=list[schemas.StoreResponse])
def get_stores(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("view_store"))
):
    return db.query(models.Store).offset(skip).limit(limit).all()


@router.get("/{store_id}", response_model=schemas.StoreResponse)
def get_store(
    store_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("view_store"))
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

    service_names = update_data.pop("services", None)

    for key, value in update_data.items():
        setattr(store, key, value)

    if service_names is not None:
        store.service_items = get_or_create_services(service_names, db)
        store.services = "|".join(service_names) if service_names else None

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


@public_router.post("/search", response_model=schemas.StoreSearchResponse)
@limiter.limit("10/minute")
@limiter.limit("100/hour")
def search_stores(
    request: Request,
    search: schemas.StoreSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Search stores by location and filters.

    Support:
    - latitude/longitude
    - address
    - postal code

    Filters:
    - radius
    - store types
    - services
    - open now
    - minimum rating
    """
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

    # if search.services:
    #     for service in search.services:
    #         query = query.filter(models.Store.services.ilike(f"%{service}%"))
    
    if search.services:
        for service in search.services:
            query = query.filter(
                models.Store.service_items.any(models.Service.name == service)
            )
            
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

    return {
        "metadata": {
            "latitude": lat,
            "longitude": lon,
            "radius_miles": radius,
            "filters": {
                "store_types": search.store_types,
                "services": search.services,
                "open_now": search.open_now,
                "min_rating": search.min_rating
            }
        },
        "results": results
    }

@router.post("/import", response_model=schemas.ImportReport)
def import_stores(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(permission_required("import_store"))
):
    required_headers = [
        "store_id", "name", "store_type", "status", "latitude", "longitude",
        "address_street", "address_city", "address_state", "address_postal_code",
        "address_country", "phone", "services", "hours_mon", "hours_tue",
        "hours_wed", "hours_thu", "hours_fri", "hours_sat", "hours_sun"
    ]

    content = file.file.read().decode("utf-8")
    csv_reader = csv.DictReader(StringIO(content))

    if csv_reader.fieldnames != required_headers:
        raise HTTPException(
            status_code=400,
            detail="CSV headers do not match required format"
        )

    created = 0
    updated = 0
    errors = []
    rows_to_process = []

    for row_number, row in enumerate(csv_reader, start=2):
        try:
            if not row["store_id"]:
                raise ValueError("store_id is required")

            if row["store_type"] not in ["flagship", "regular", "outlet", "express"]:
                raise ValueError("Invalid store_type")

            if row["status"] not in ["active", "inactive", "temporarily_closed"]:
                raise ValueError("Invalid status")

            if row["latitude"]:
                row["latitude"] = float(row["latitude"])

                if row["latitude"] < -90 or row["latitude"] > 90:
                    raise ValueError("latitude must be between -90 and 90")
            else:
                row["latitude"] = None

            if row["longitude"]:
                row["longitude"] = float(row["longitude"])

                if row["longitude"] < -180 or row["longitude"] > 180:
                    raise ValueError("longitude must be between -180 and 180")
            else:
                row["longitude"] = None

            if row["latitude"] is None or row["longitude"] is None:
                full_address = (
                    f"{row['address_street']}, {row['address_city']}, "
                    f"{row['address_state']} {row['address_postal_code']}, "
                    f"{row['address_country']}"
                )

                location = geocode_location(full_address)

                if not location:
                    raise ValueError("Address could not be geocoded")

                row["latitude"] = location["latitude"]
                row["longitude"] = location["longitude"]

            rows_to_process.append((row_number, row))

        except Exception as e:
            errors.append({
                "row_number": row_number,
                "error": str(e)
            })

    if errors:
        return {
            "total_rows": len(rows_to_process) + len(errors),
            "created": 0,
            "updated": 0,
            "failed": len(errors),
            "errors": errors
        }

    try:
        for row_number, row in rows_to_process:
            existing = db.query(models.Store).filter(
                models.Store.store_id == row["store_id"]
            ).first()

            if existing:
                for key, value in row.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)

                updated += 1

            else:
                new_store = models.Store(**row)
                db.add(new_store)
                created += 1

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"CSV import failed and rolled back: {str(e)}"
        )

    return {
        "total_rows": len(rows_to_process),
        "created": created,
        "updated": updated,
        "failed": 0,
        "errors": []
    }


@router.get("/export/csv")
def export_stores_csv(
    db: Session = Depends(get_db)
):
    """
    Export all stores as CSV file.
    """
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