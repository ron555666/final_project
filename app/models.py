from sqlalchemy import Column, String, Float, Index, ForeignKey, Table, Boolean, DateTime, Integer
from sqlalchemy.orm import relationship
from app.database import Base

store_services = Table(
    "store_services",
    Base.metadata,
    Column("store_id", String, ForeignKey("stores.store_id"), primary_key=True),
    Column("service_id", String, ForeignKey("services.service_id"), primary_key=True)
)

class Store(Base):
    __tablename__ = "stores"
    
    store_id = Column(String, primary_key=True, index = True)
    
    name = Column(String, nullable=False)
    store_type = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="active", index = True)
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    address_street = Column(String, nullable=False)
    address_city = Column(String, nullable=False)
    address_state = Column(String(2), nullable=False)
    address_postal_code = Column(String(5), nullable=False, index = True)
    address_country = Column(String(3), nullable=False, default="USA")
    
    phone = Column(String, nullable=True)
    services = Column(String, nullable=True)
    service_items = relationship(
    "Service",
    secondary=store_services,
    back_populates="stores"
)
    
    hours_mon = Column(String, nullable=True)
    hours_tue = Column(String, nullable=True)
    hours_wed = Column(String, nullable=True)
    hours_thu = Column(String, nullable=True)
    hours_fri = Column(String, nullable=True)
    hours_sat = Column(String, nullable=True)
    hours_sun = Column(String, nullable=True)
    
Index("idx_store_lat_lon", Store.latitude, Store.longitude)

class Service(Base):
    __tablename__ = "services"

    service_id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)

    stores = relationship(
    "Store",
    secondary=store_services,
    back_populates="service_items"
    )


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String, ForeignKey("roles.role_id"), primary_key=True),
    Column("permission_id", String, ForeignKey("permissions.permission_id"), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    role_id = Column(String, ForeignKey("roles.role_id"), nullable=False)
    role = relationship("Role")

    status = Column(String, nullable=False, default="active")
class Role(Base):
    __tablename__ = "roles"

    role_id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )

class Permission(Base):
    __tablename__ = "permissions"

    permission_id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )
    
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    token_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    token_hash = Column(String, nullable=False, index=True)
    revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    
    
class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.store_id"), nullable=False, index=True)

    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    flagged = Column(Boolean, default=False)
    
    
Index("idx_stores_lat_lon", Store.latitude, Store.longitude)
Index("idx_stores_type", Store.store_type)
Index("idx_stores_postal_code", Store.address_postal_code)

Index(
    "idx_stores_active",
    Store.status,
    postgresql_where=(Store.status == "active")
)

Index("idx_users_email", User.email)
Index("idx_refresh_token_hash", RefreshToken.token_hash)
