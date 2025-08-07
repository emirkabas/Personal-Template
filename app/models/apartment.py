"""
Apartment model for storing scraped apartment listings.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime
from .base import Base

class Apartment(Base):
    """SQLAlchemy model for apartment listings."""
    
    __tablename__ = "apartments"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Source information
    source = Column(String(50), nullable=False, index=True)  # nestpick, boligzonen, lejebolig
    external_id = Column(String(255), index=True)  # ID from the source website
    source_url = Column(Text, nullable=False)  # Original listing URL
    
    # Basic apartment information
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Location information
    address = Column(String(255))
    city = Column(String(100), nullable=False, index=True)
    postal_code = Column(String(20))
    country = Column(String(50), default="Denmark")
    neighborhood = Column(String(100))
    
    # Geographic coordinates
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Property details
    price = Column(Float, nullable=False, index=True)  # Monthly rent
    currency = Column(String(10), default="DKK")
    deposit = Column(Float)  # Security deposit
    
    # Size and layout
    size_sqm = Column(Float, index=True)  # Size in square meters
    rooms = Column(Integer, index=True)  # Number of rooms
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    
    # Availability
    available_from = Column(DateTime)
    available_until = Column(DateTime)
    is_available = Column(Boolean, default=True, index=True)
    
    # Property features
    furnished = Column(Boolean)
    pets_allowed = Column(Boolean)
    balcony = Column(Boolean)
    parking = Column(Boolean)
    elevator = Column(Boolean)
    
    # Additional information
    property_type = Column(String(50))  # apartment, house, room, studio
    amenities = Column(JSON)  # List of amenities
    images = Column(JSON)  # List of image URLs
    contact_info = Column(JSON)  # Contact information
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_scraped = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, index=True)  # Whether listing is still active
    
    # Additional data from specific sources
    extra_data = Column(JSON)  # For storing source-specific data
    
    def __repr__(self):
        return f"<Apartment(id={self.id}, title='{self.title}', price={self.price}, city='{self.city}')>"


class ApartmentBase(BaseModel):
    """Base Pydantic model for apartment data."""
    
    source: str
    external_id: Optional[str] = None
    source_url: str
    title: str
    description: Optional[str] = None
    
    # Location
    address: Optional[str] = None
    city: str
    postal_code: Optional[str] = None
    country: str = "Denmark"
    neighborhood: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Price and property details
    price: float
    currency: str = "DKK"
    deposit: Optional[float] = None
    size_sqm: Optional[float] = None
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    
    # Availability
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    is_available: bool = True
    
    # Features
    furnished: Optional[bool] = None
    pets_allowed: Optional[bool] = None
    balcony: Optional[bool] = None
    parking: Optional[bool] = None
    elevator: Optional[bool] = None
    
    # Additional
    property_type: Optional[str] = None
    amenities: Optional[list] = None
    images: Optional[list] = None
    contact_info: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ApartmentCreate(ApartmentBase):
    """Pydantic model for creating apartments."""
    pass


class ApartmentUpdate(BaseModel):
    """Pydantic model for updating apartments."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_available: Optional[bool] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    size_sqm: Optional[float] = None
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    furnished: Optional[bool] = None
    pets_allowed: Optional[bool] = None
    balcony: Optional[bool] = None
    parking: Optional[bool] = None
    elevator: Optional[bool] = None
    amenities: Optional[list] = None
    images: Optional[list] = None
    contact_info: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None


class ApartmentResponse(ApartmentBase):
    """Pydantic model for apartment responses."""
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_scraped: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True


class ApartmentFilter(BaseModel):
    """Pydantic model for filtering apartments."""
    
    city: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_size: Optional[float] = None
    max_size: Optional[float] = None
    min_rooms: Optional[int] = None
    max_rooms: Optional[int] = None
    property_type: Optional[str] = None
    furnished: Optional[bool] = None
    pets_allowed: Optional[bool] = None
    balcony: Optional[bool] = None
    parking: Optional[bool] = None
    elevator: Optional[bool] = None
    available_only: bool = True
    source: Optional[str] = None
    
    # Pagination
    page: int = 1
    page_size: int = 20
    
    # Sorting
    sort_by: str = "created_at"
    sort_order: str = "desc"  # asc or desc