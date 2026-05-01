from pydantic import BaseModel, Field, computed_field
from typing import Optional, List


class StoreCreate(BaseModel):
    store_id: str
    name: str
    store_type: str
    status: str

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    address_street: str
    address_city: str
    address_state: str
    address_postal_code: str
    address_country: str

    phone: Optional[str] = None
    services: Optional[List[str]] = None

    hours_mon: Optional[str] = None
    hours_tue: Optional[str] = None
    hours_wed: Optional[str] = None
    hours_thu: Optional[str] = None
    hours_fri: Optional[str] = None
    hours_sat: Optional[str] = None
    hours_sun: Optional[str] = None


class StoreResponse(StoreCreate):
    services: Optional[str] = None

    class Config:
        from_attributes = True

class StoreUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    services: Optional[List[str]] = None
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
    average_rating: float = 0
    review_count: int = 0


class StoreSearchMetadata(BaseModel):
    latitude: float
    longitude: float
    radius_miles: float
    filters: dict


class StoreSearchResponse(BaseModel):
    metadata: StoreSearchMetadata
    results: List[StoreSearchResult]
    
    
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
    
class ImportErrorDetail(BaseModel):
    row_number: int
    error: str


class ImportReport(BaseModel):
    total_rows: int
    created: int
    updated: int
    failed: int
    errors: List[ImportErrorDetail]
    
    
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
    
    
    
    
class UserCreate(BaseModel):
    email: str
    password: str
    role_id: str
    status: str = "active"


class UserResponse(BaseModel):
    user_id: str
    email: str
    role_id: str
    status: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    role_id: Optional[str] = None
    status: Optional[str] = None