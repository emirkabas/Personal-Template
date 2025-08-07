"""
Apartment endpoints for searching, filtering, and managing apartment listings.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import math

from app.database.session import get_db
from app.database.crud import ApartmentCRUD
from app.models.apartment import (
    ApartmentResponse, 
    ApartmentFilter, 
    ApartmentCreate,
    ApartmentUpdate
)

router = APIRouter()

@router.get("/apartments", response_model=Dict[str, Any])
async def search_apartments(
    # Location filters
    city: Optional[str] = Query(None, description="Filter by city"),
    
    # Price filters
    min_price: Optional[float] = Query(None, description="Minimum price per month"),
    max_price: Optional[float] = Query(None, description="Maximum price per month"),
    
    # Size filters
    min_size: Optional[float] = Query(None, description="Minimum size in square meters"),
    max_size: Optional[float] = Query(None, description="Maximum size in square meters"),
    
    # Room filters
    min_rooms: Optional[int] = Query(None, description="Minimum number of rooms"),
    max_rooms: Optional[int] = Query(None, description="Maximum number of rooms"),
    
    # Property filters
    property_type: Optional[str] = Query(None, description="Property type (apartment, house, room, studio)"),
    furnished: Optional[bool] = Query(None, description="Furnished status"),
    pets_allowed: Optional[bool] = Query(None, description="Pets allowed"),
    balcony: Optional[bool] = Query(None, description="Has balcony"),
    parking: Optional[bool] = Query(None, description="Has parking"),
    elevator: Optional[bool] = Query(None, description="Has elevator"),
    
    # Availability
    available_only: bool = Query(True, description="Show only available apartments"),
    
    # Source filter
    source: Optional[str] = Query(None, description="Filter by source (nestpick, boligzonen, lejebolig)"),
    
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    
    # Sorting
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    
    db: Session = Depends(get_db)
):
    """
    Search and filter apartment listings.
    
    Returns paginated results with filtering options for location, price, size, and amenities.
    """
    try:
        # Create filter object
        filters = ApartmentFilter(
            city=city,
            min_price=min_price,
            max_price=max_price,
            min_size=min_size,
            max_size=max_size,
            min_rooms=min_rooms,
            max_rooms=max_rooms,
            property_type=property_type,
            furnished=furnished,
            pets_allowed=pets_allowed,
            balcony=balcony,
            parking=parking,
            elevator=elevator,
            available_only=available_only,
            source=source,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get filtered apartments
        apartments = ApartmentCRUD.get_filtered(db, filters)
        
        # Get total count for pagination
        total_count = ApartmentCRUD.count_filtered(db, filters)
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / page_size)
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "apartments": [ApartmentResponse.model_validate(apt) for apt in apartments],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            },
            "filters_applied": filters.model_dump(exclude_unset=True)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching apartments: {str(e)}")

@router.get("/apartments/{apartment_id}", response_model=ApartmentResponse)
async def get_apartment(apartment_id: int, db: Session = Depends(get_db)):
    """Get a specific apartment by ID."""
    apartment = ApartmentCRUD.get_by_id(db, apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    return ApartmentResponse.model_validate(apartment)

@router.post("/apartments", response_model=ApartmentResponse)
async def create_apartment(apartment: ApartmentCreate, db: Session = Depends(get_db)):
    """Create a new apartment listing."""
    try:
        created_apartment = ApartmentCRUD.create(db, apartment)
        return ApartmentResponse.model_validate(created_apartment)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating apartment: {str(e)}")

@router.put("/apartments/{apartment_id}", response_model=ApartmentResponse)
async def update_apartment(
    apartment_id: int, 
    apartment_update: ApartmentUpdate, 
    db: Session = Depends(get_db)
):
    """Update an apartment listing."""
    updated_apartment = ApartmentCRUD.update(db, apartment_id, apartment_update)
    if not updated_apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    return ApartmentResponse.model_validate(updated_apartment)

@router.delete("/apartments/{apartment_id}")
async def delete_apartment(apartment_id: int, db: Session = Depends(get_db)):
    """Delete an apartment listing."""
    success = ApartmentCRUD.delete(db, apartment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    return {"message": "Apartment deleted successfully"}

@router.post("/apartments/{apartment_id}/deactivate")
async def deactivate_apartment(apartment_id: int, db: Session = Depends(get_db)):
    """Mark an apartment as inactive instead of deleting it."""
    apartment = ApartmentCRUD.mark_inactive(db, apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    
    return {"message": "Apartment marked as inactive"}

@router.get("/apartments/cities", response_model=List[str])
async def get_cities(db: Session = Depends(get_db)):
    """Get list of all available cities."""
    cities = ApartmentCRUD.get_cities(db)
    return sorted(cities)

@router.get("/apartments/stats", response_model=Dict[str, Any])
async def get_apartment_stats(db: Session = Depends(get_db)):
    """Get statistics about apartment listings."""
    try:
        stats = ApartmentCRUD.get_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@router.get("/apartments/search/advanced")
async def advanced_search(
    # Text search
    query: Optional[str] = Query(None, description="Search in title and description"),
    
    # Location
    city: Optional[str] = Query(None, description="City name"),
    postal_code: Optional[str] = Query(None, description="Postal code"),
    
    # Price range with currency
    price_min: Optional[float] = Query(None, description="Minimum price"),
    price_max: Optional[float] = Query(None, description="Maximum price"),
    currency: Optional[str] = Query(None, description="Currency (DKK, EUR, USD)"),
    
    # Size and rooms
    size_min: Optional[float] = Query(None, description="Minimum size in m²"),
    size_max: Optional[float] = Query(None, description="Maximum size in m²"),
    rooms_min: Optional[int] = Query(None, description="Minimum rooms"),
    rooms_max: Optional[int] = Query(None, description="Maximum rooms"),
    bedrooms_min: Optional[int] = Query(None, description="Minimum bedrooms"),
    bedrooms_max: Optional[int] = Query(None, description="Maximum bedrooms"),
    
    # Property features
    property_types: Optional[str] = Query(None, description="Comma-separated property types"),
    furnished: Optional[bool] = Query(None, description="Furnished apartments only"),
    pets_allowed: Optional[bool] = Query(None, description="Pet-friendly apartments"),
    has_balcony: Optional[bool] = Query(None, description="Apartments with balcony"),
    has_parking: Optional[bool] = Query(None, description="Apartments with parking"),
    has_elevator: Optional[bool] = Query(None, description="Apartments with elevator"),
    
    # Source and availability
    sources: Optional[str] = Query(None, description="Comma-separated sources"),
    available_only: bool = Query(True, description="Available apartments only"),
    
    # Sorting and pagination
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    
    db: Session = Depends(get_db)
):
    """
    Advanced search with multiple criteria and text search.
    """
    try:
        # Parse comma-separated values
        property_type_list = property_types.split(',') if property_types else None
        source_list = sources.split(',') if sources else None
        
        # This would require a more sophisticated search implementation
        # For now, we'll use the basic filter functionality
        filters = ApartmentFilter(
            city=city,
            min_price=price_min,
            max_price=price_max,
            min_size=size_min,
            max_size=size_max,
            min_rooms=rooms_min,
            max_rooms=rooms_max,
            property_type=property_type_list[0] if property_type_list else None,
            furnished=furnished,
            pets_allowed=pets_allowed,
            balcony=has_balcony,
            parking=has_parking,
            elevator=has_elevator,
            available_only=available_only,
            source=source_list[0] if source_list else None,
            page=page,
            page_size=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        apartments = ApartmentCRUD.get_filtered(db, filters)
        total_count = ApartmentCRUD.count_filtered(db, filters)
        
        # TODO: Implement text search in title/description
        # This would require full-text search capabilities
        
        return {
            "results": [ApartmentResponse.model_validate(apt) for apt in apartments],
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": math.ceil(total_count / limit),
            "query_info": {
                "text_query": query,
                "filters_applied": filters.model_dump(exclude_unset=True)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in advanced search: {str(e)}")