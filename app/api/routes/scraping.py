"""
Scraping endpoints for triggering and monitoring scraping operations.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from loguru import logger

from app.scrapers.manager import ScraperManager

router = APIRouter()

# Request/Response models
class ScrapingRequest(BaseModel):
    sources: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    max_pages: int = 5
    save_to_db: bool = True
    use_async: bool = False

class ScrapingResponse(BaseModel):
    message: str
    task_id: Optional[str] = None
    results: Optional[Dict[str, Any]] = None

# Global scraper manager instance
scraper_manager = ScraperManager()

@router.get("/scraping/sources")
async def get_available_sources() -> Dict[str, Any]:
    """Get list of available scraping sources."""
    return {
        "sources": scraper_manager.get_available_scrapers(),
        "description": "Available apartment scraping sources"
    }

@router.post("/scraping/run", response_model=ScrapingResponse)
async def run_scraping(request: ScrapingRequest):
    """
    Run apartment scraping for specified sources and locations.
    
    This is a synchronous operation that will return results immediately.
    For large scraping operations, consider using the async endpoint.
    """
    try:
        logger.info(f"Starting scraping with request: {request}")
        
        # Validate sources
        available_sources = scraper_manager.get_available_scrapers()
        if request.sources:
            invalid_sources = [s for s in request.sources if s not in available_sources]
            if invalid_sources:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid sources: {invalid_sources}. Available: {available_sources}"
                )
        
        # Run scraping
        results = scraper_manager.scrape_all_sources(
            locations=request.locations,
            max_pages=request.max_pages,
            save_to_db=request.save_to_db,
            use_async=request.use_async,
            sources=request.sources
        )
        
        return ScrapingResponse(
            message="Scraping completed successfully",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error in scraping operation: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@router.post("/scraping/run-async", response_model=ScrapingResponse)
async def run_scraping_async(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Run apartment scraping asynchronously in the background.
    
    Returns immediately with a task ID for tracking progress.
    """
    try:
        # For now, we'll run the async version directly
        # In a production environment, you'd want to use a proper task queue like Celery
        logger.info(f"Starting async scraping with request: {request}")
        
        # Validate sources
        available_sources = scraper_manager.get_available_scrapers()
        if request.sources:
            invalid_sources = [s for s in request.sources if s not in available_sources]
            if invalid_sources:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid sources: {invalid_sources}. Available: {available_sources}"
                )
        
        # Run async scraping
        results = await scraper_manager.scrape_all_sources_async(
            locations=request.locations,
            max_pages=request.max_pages,
            save_to_db=request.save_to_db,
            sources=request.sources
        )
        
        return ScrapingResponse(
            message="Async scraping completed",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error in async scraping operation: {e}")
        raise HTTPException(status_code=500, detail=f"Async scraping failed: {str(e)}")

@router.post("/scraping/run-source/{source}", response_model=ScrapingResponse)
async def run_single_source_scraping(
    source: str,
    locations: Optional[List[str]] = Query(None),
    max_pages: int = Query(5),
    save_to_db: bool = Query(True),
    use_async: bool = Query(False)
):
    """
    Run scraping for a specific source.
    """
    try:
        # Validate source
        available_sources = scraper_manager.get_available_scrapers()
        if source not in available_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source: {source}. Available: {available_sources}"
            )
        
        logger.info(f"Starting scraping for source: {source}")
        
        # Run scraping for single source
        result = scraper_manager.scrape_source(
            source=source,
            locations=locations,
            max_pages=max_pages,
            save_to_db=save_to_db,
            use_async=use_async
        )
        
        return ScrapingResponse(
            message=f"Scraping completed for {source}",
            results=result
        )
        
    except Exception as e:
        logger.error(f"Error scraping {source}: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping {source} failed: {str(e)}")

@router.get("/scraping/stats")
async def get_scraping_stats() -> Dict[str, Any]:
    """
    Get current scraping statistics.
    """
    try:
        stats = scraper_manager.get_scraping_statistics()
        return {
            "current_session_stats": stats,
            "available_sources": scraper_manager.get_available_scrapers()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@router.post("/scraping/reset-stats")
async def reset_scraping_stats():
    """
    Reset scraping statistics.
    """
    try:
        scraper_manager.reset_statistics()
        return {"message": "Scraping statistics reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting stats: {str(e)}")

@router.get("/scraping/test/{source}")
async def test_scraper(source: str):
    """
    Test a specific scraper with minimal scraping (1 page, 1 location).
    """
    try:
        # Validate source
        available_sources = scraper_manager.get_available_scrapers()
        if source not in available_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source: {source}. Available: {available_sources}"
            )
        
        logger.info(f"Testing scraper: {source}")
        
        # Test with minimal parameters
        result = scraper_manager.scrape_source(
            source=source,
            locations=["copenhagen"] if source in ["boligzonen", "lejebolig"] else [""],
            max_pages=1,
            save_to_db=False,
            use_async=False
        )
        
        return {
            "message": f"Test scraping completed for {source}",
            "test_results": result,
            "status": "success" if result.get("scraped_count", 0) > 0 else "no_results"
        }
        
    except Exception as e:
        logger.error(f"Error testing {source}: {e}")
        raise HTTPException(status_code=500, detail=f"Test scraping {source} failed: {str(e)}")

@router.post("/scraping/locations")
async def scrape_specific_locations(
    locations: List[str],
    sources: Optional[List[str]] = None,
    max_pages: int = 5,
    save_to_db: bool = True
):
    """
    Scrape apartments from specific locations across all or selected sources.
    """
    try:
        logger.info(f"Starting location-specific scraping for: {locations}")
        
        # Validate sources if provided
        if sources:
            available_sources = scraper_manager.get_available_scrapers()
            invalid_sources = [s for s in sources if s not in available_sources]
            if invalid_sources:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid sources: {invalid_sources}. Available: {available_sources}"
                )
        
        # Run scraping
        results = scraper_manager.scrape_all_sources(
            locations=locations,
            max_pages=max_pages,
            save_to_db=save_to_db,
            use_async=False,
            sources=sources
        )
        
        return {
            "message": f"Location scraping completed for {locations}",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in location scraping: {e}")
        raise HTTPException(status_code=500, detail=f"Location scraping failed: {str(e)}")

@router.get("/scraping/status")
async def get_scraping_status():
    """
    Get current scraping system status and health.
    """
    try:
        stats = scraper_manager.get_scraping_statistics()
        available_sources = scraper_manager.get_available_scrapers()
        
        return {
            "status": "healthy",
            "available_sources": available_sources,
            "current_stats": stats,
            "system_info": {
                "total_sources": len(available_sources),
                "last_run_stats": stats
            }
        }
    except Exception as e:
        logger.error(f"Error getting scraping status: {e}")
        return {
            "status": "error",
            "message": str(e)
        }