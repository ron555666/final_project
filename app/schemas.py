from pydantic import BaseModel, Field
from typing import Optional, List


class StoreCreate(BaseModel):
    store_id: str
    name: str
    store_type: str
    status: str

    latitude: float
    longitude: float

    address_street: str
    address_city: str
    address_state: str
    address_postal_code: str
    address_country: str

    phone: Optional[str] = None
    services: Optional[str] = None

    hours_mon: Optional[str] = None
    hours_tue: Optional[str] = None
    hours_wed: Optional[str] = None
    hours_thu: Optional[str] = None
    hours_fri: Optional[str] = None
    hours_sat: Optional[str] = None
    hours_sun: Optional[str] = None


class StoreResponse(StoreCreate):
    class Config:
        from_attributes = True


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    services: Optional[str] = None
    status: Optional[str] = None

    hours_mon: Optional[str] = None
    hours_tue: Optional[str] = None
    hours_wed: Optional[str] = None
    hours_thu: Optional[str] = None
    hours_fri: Optional[str] = None
    hours_sat: Optional[str] = None
    hours_sun: Optional[str] = None


class StoreSearchRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    address: Optional[str] = None
    postal_code: Optional[str] = None

    radius_miles: Optional[float] = 10
    store_types: Optional[List[str]] = None
    services: Optional[List[str]] = None
    open_now: Optional[bool] = None
    min_rating: Optional[float] = None


class StoreSearchResult(StoreResponse):
    distance_miles: float
    is_open_now: bool
    
    
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
    
class ImportReport(BaseModel):
    created: int
    updated: int
    failed: int
    
    
class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(ReviewCreate):
    review_id: str
    store_id: str
    flagged: bool

    class Config:
        from_attributes = True


class RatingSummary(BaseModel):
    store_id: str
    average_rating: float
    review_count: int