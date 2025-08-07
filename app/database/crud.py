"""
CRUD operations for apartment data.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from app.models.apartment import Apartment, ApartmentCreate, ApartmentUpdate, ApartmentFilter
from loguru import logger

class ApartmentCRUD:
    """CRUD operations for apartments."""
    
    @staticmethod
    def create(db: Session, apartment_data: ApartmentCreate) -> Apartment:
        """Create a new apartment listing."""
        try:
            db_apartment = Apartment(**apartment_data.model_dump())
            db.add(db_apartment)
            db.commit()
            db.refresh(db_apartment)
            logger.info(f"Created apartment: {db_apartment.id}")
            return db_apartment
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating apartment: {e}")
            raise
    
    @staticmethod
    def get_by_id(db: Session, apartment_id: int) -> Optional[Apartment]:
        """Get apartment by ID."""
        return db.query(Apartment).filter(Apartment.id == apartment_id).first()
    
    @staticmethod
    def get_by_external_id(db: Session, source: str, external_id: str) -> Optional[Apartment]:
        """Get apartment by external ID and source."""
        return db.query(Apartment).filter(
            and_(
                Apartment.source == source,
                Apartment.external_id == external_id
            )
        ).first()
    
    @staticmethod
    def get_by_url(db: Session, source_url: str) -> Optional[Apartment]:
        """Get apartment by source URL."""
        return db.query(Apartment).filter(Apartment.source_url == source_url).first()
    
    @staticmethod
    def update(db: Session, apartment_id: int, update_data: ApartmentUpdate) -> Optional[Apartment]:
        """Update an apartment."""
        try:
            db_apartment = ApartmentCRUD.get_by_id(db, apartment_id)
            if not db_apartment:
                return None
            
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(db_apartment, field, value)
            
            # Update the last_scraped timestamp
            db_apartment.last_scraped = func.now()
            
            db.commit()
            db.refresh(db_apartment)
            logger.info(f"Updated apartment: {apartment_id}")
            return db_apartment
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating apartment {apartment_id}: {e}")
            raise
    
    @staticmethod
    def delete(db: Session, apartment_id: int) -> bool:
        """Delete an apartment."""
        try:
            db_apartment = ApartmentCRUD.get_by_id(db, apartment_id)
            if not db_apartment:
                return False
            
            db.delete(db_apartment)
            db.commit()
            logger.info(f"Deleted apartment: {apartment_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting apartment {apartment_id}: {e}")
            raise
    
    @staticmethod
    def mark_inactive(db: Session, apartment_id: int) -> Optional[Apartment]:
        """Mark an apartment as inactive instead of deleting."""
        try:
            db_apartment = ApartmentCRUD.get_by_id(db, apartment_id)
            if not db_apartment:
                return None
            
            db_apartment.is_active = False
            db_apartment.is_available = False
            db.commit()
            db.refresh(db_apartment)
            logger.info(f"Marked apartment as inactive: {apartment_id}")
            return db_apartment
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking apartment {apartment_id} as inactive: {e}")
            raise
    
    @staticmethod
    def get_filtered(db: Session, filters: ApartmentFilter) -> List[Apartment]:
        """Get apartments with filters applied."""
        query = db.query(Apartment)
        
        # Apply filters
        conditions = []
        
        if filters.city:
            conditions.append(Apartment.city.ilike(f"%{filters.city}%"))
        
        if filters.min_price is not None:
            conditions.append(Apartment.price >= filters.min_price)
        
        if filters.max_price is not None:
            conditions.append(Apartment.price <= filters.max_price)
        
        if filters.min_size is not None:
            conditions.append(Apartment.size_sqm >= filters.min_size)
        
        if filters.max_size is not None:
            conditions.append(Apartment.size_sqm <= filters.max_size)
        
        if filters.min_rooms is not None:
            conditions.append(Apartment.rooms >= filters.min_rooms)
        
        if filters.max_rooms is not None:
            conditions.append(Apartment.rooms <= filters.max_rooms)
        
        if filters.property_type:
            conditions.append(Apartment.property_type == filters.property_type)
        
        if filters.furnished is not None:
            conditions.append(Apartment.furnished == filters.furnished)
        
        if filters.pets_allowed is not None:
            conditions.append(Apartment.pets_allowed == filters.pets_allowed)
        
        if filters.balcony is not None:
            conditions.append(Apartment.balcony == filters.balcony)
        
        if filters.parking is not None:
            conditions.append(Apartment.parking == filters.parking)
        
        if filters.elevator is not None:
            conditions.append(Apartment.elevator == filters.elevator)
        
        if filters.available_only:
            conditions.append(Apartment.is_available == True)
            conditions.append(Apartment.is_active == True)
        
        if filters.source:
            conditions.append(Apartment.source == filters.source)
        
        # Apply all conditions
        if conditions:
            query = query.filter(and_(*conditions))
        
        # Apply sorting
        if filters.sort_order.lower() == "desc":
            order_func = desc
        else:
            order_func = asc
        
        if hasattr(Apartment, filters.sort_by):
            query = query.order_by(order_func(getattr(Apartment, filters.sort_by)))
        else:
            query = query.order_by(desc(Apartment.created_at))
        
        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        query = query.offset(offset).limit(filters.page_size)
        
        return query.all()
    
    @staticmethod
    def count_filtered(db: Session, filters: ApartmentFilter) -> int:
        """Count apartments with filters applied."""
        query = db.query(func.count(Apartment.id))
        
        # Apply same filters as get_filtered but without pagination and sorting
        conditions = []
        
        if filters.city:
            conditions.append(Apartment.city.ilike(f"%{filters.city}%"))
        
        if filters.min_price is not None:
            conditions.append(Apartment.price >= filters.min_price)
        
        if filters.max_price is not None:
            conditions.append(Apartment.price <= filters.max_price)
        
        if filters.min_size is not None:
            conditions.append(Apartment.size_sqm >= filters.min_size)
        
        if filters.max_size is not None:
            conditions.append(Apartment.size_sqm <= filters.max_size)
        
        if filters.min_rooms is not None:
            conditions.append(Apartment.rooms >= filters.min_rooms)
        
        if filters.max_rooms is not None:
            conditions.append(Apartment.rooms <= filters.max_rooms)
        
        if filters.property_type:
            conditions.append(Apartment.property_type == filters.property_type)
        
        if filters.furnished is not None:
            conditions.append(Apartment.furnished == filters.furnished)
        
        if filters.pets_allowed is not None:
            conditions.append(Apartment.pets_allowed == filters.pets_allowed)
        
        if filters.balcony is not None:
            conditions.append(Apartment.balcony == filters.balcony)
        
        if filters.parking is not None:
            conditions.append(Apartment.parking == filters.parking)
        
        if filters.elevator is not None:
            conditions.append(Apartment.elevator == filters.elevator)
        
        if filters.available_only:
            conditions.append(Apartment.is_available == True)
            conditions.append(Apartment.is_active == True)
        
        if filters.source:
            conditions.append(Apartment.source == filters.source)
        
        # Apply all conditions
        if conditions:
            query = query.filter(and_(*conditions))
        
        return query.scalar()
    
    @staticmethod
    def get_cities(db: Session) -> List[str]:
        """Get list of all unique cities."""
        return [city[0] for city in db.query(Apartment.city).distinct().all() if city[0]]
    
    @staticmethod
    def get_stats(db: Session) -> Dict[str, Any]:
        """Get statistics about apartments."""
        total_apartments = db.query(func.count(Apartment.id)).scalar()
        active_apartments = db.query(func.count(Apartment.id)).filter(
            and_(Apartment.is_active == True, Apartment.is_available == True)
        ).scalar()
        
        avg_price = db.query(func.avg(Apartment.price)).filter(
            Apartment.is_active == True
        ).scalar()
        
        price_range = db.query(
            func.min(Apartment.price),
            func.max(Apartment.price)
        ).filter(Apartment.is_active == True).first()
        
        sources = db.query(Apartment.source, func.count(Apartment.id)).filter(
            Apartment.is_active == True
        ).group_by(Apartment.source).all()
        
        cities = db.query(Apartment.city, func.count(Apartment.id)).filter(
            Apartment.is_active == True
        ).group_by(Apartment.city).order_by(desc(func.count(Apartment.id))).limit(10).all()
        
        return {
            "total_apartments": total_apartments,
            "active_apartments": active_apartments,
            "average_price": float(avg_price) if avg_price else 0,
            "min_price": float(price_range[0]) if price_range[0] else 0,
            "max_price": float(price_range[1]) if price_range[1] else 0,
            "by_source": {source: count for source, count in sources},
            "top_cities": {city: count for city, count in cities}
        }
    
    @staticmethod
    def upsert(db: Session, apartment_data: ApartmentCreate) -> Apartment:
        """Insert or update apartment based on source and external_id or URL."""
        try:
            # Try to find existing apartment by external_id first
            existing = None
            if apartment_data.external_id:
                existing = ApartmentCRUD.get_by_external_id(
                    db, apartment_data.source, apartment_data.external_id
                )
            
            # If not found by external_id, try by URL
            if not existing:
                existing = ApartmentCRUD.get_by_url(db, apartment_data.source_url)
            
            if existing:
                # Update existing apartment
                update_data = ApartmentUpdate(**apartment_data.model_dump(exclude_unset=True))
                return ApartmentCRUD.update(db, existing.id, update_data)
            else:
                # Create new apartment
                return ApartmentCRUD.create(db, apartment_data)
        except Exception as e:
            logger.error(f"Error in upsert operation: {e}")
            raise