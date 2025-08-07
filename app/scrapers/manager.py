"""
Scraper manager to coordinate all apartment scrapers.
"""
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from loguru import logger

from .nestpick import NestpickScraper
from .boligzonen import BoligZonenScraper
from .lejebolig import LejeboligScraper
from app.models.apartment import ApartmentCreate
from app.database.crud import ApartmentCRUD
from app.database.session import get_db

class ScraperManager:
    """Manager for all apartment scrapers."""
    
    def __init__(self):
        self.scrapers = {
            'nestpick': NestpickScraper,
            'boligzonen': BoligZonenScraper,
            'lejebolig': LejeboligScraper
        }
        self.results = {
            'total_scraped': 0,
            'total_saved': 0,
            'by_source': {},
            'errors': []
        }
    
    def get_available_scrapers(self) -> List[str]:
        """Get list of available scraper names."""
        return list(self.scrapers.keys())
    
    def scrape_source(
        self, 
        source: str, 
        locations: List[str] = None, 
        max_pages: int = 10,
        save_to_db: bool = True,
        use_async: bool = False
    ) -> Dict[str, Any]:
        """
        Scrape apartments from a specific source.
        
        Args:
            source: Name of the scraper source
            locations: List of locations to scrape
            max_pages: Maximum pages to scrape per location
            save_to_db: Whether to save results to database
            use_async: Whether to use async scraping
            
        Returns:
            Dictionary with scraping results
        """
        if source not in self.scrapers:
            raise ValueError(f"Unknown scraper source: {source}")
        
        logger.info(f"Starting scraping from {source}")
        
        try:
            # Initialize scraper
            scraper_class = self.scrapers[source]
            
            with scraper_class() as scraper:
                # Scrape apartments
                if use_async:
                    apartments = asyncio.run(
                        scraper.scrape_all_async(locations, max_pages)
                    )
                else:
                    apartments = scraper.scrape_all(locations, max_pages)
                
                # Save to database if requested
                saved_count = 0
                if save_to_db and apartments:
                    saved_count = self._save_apartments_to_db(apartments)
                
                # Update results
                result = {
                    'source': source,
                    'scraped_count': len(apartments),
                    'saved_count': saved_count,
                    'apartments': apartments if not save_to_db else None
                }
                
                self.results['total_scraped'] += len(apartments)
                self.results['total_saved'] += saved_count
                self.results['by_source'][source] = result
                
                logger.info(
                    f"Completed scraping {source}: "
                    f"{len(apartments)} scraped, {saved_count} saved"
                )
                
                return result
                
        except Exception as e:
            error_msg = f"Error scraping {source}: {e}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            
            return {
                'source': source,
                'scraped_count': 0,
                'saved_count': 0,
                'error': str(e)
            }
    
    def scrape_all_sources(
        self, 
        locations: List[str] = None, 
        max_pages: int = 10,
        save_to_db: bool = True,
        use_async: bool = False,
        sources: List[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape apartments from all or specified sources.
        
        Args:
            locations: List of locations to scrape
            max_pages: Maximum pages to scrape per location
            save_to_db: Whether to save results to database
            use_async: Whether to use async scraping
            sources: Specific sources to scrape (if None, scrape all)
            
        Returns:
            Dictionary with overall scraping results
        """
        # Reset results
        self.results = {
            'total_scraped': 0,
            'total_saved': 0,
            'by_source': {},
            'errors': []
        }
        
        # Determine which sources to scrape
        sources_to_scrape = sources if sources else list(self.scrapers.keys())
        
        logger.info(f"Starting scraping from {len(sources_to_scrape)} sources: {sources_to_scrape}")
        
        # Scrape each source
        for source in sources_to_scrape:
            try:
                self.scrape_source(
                    source=source,
                    locations=locations,
                    max_pages=max_pages,
                    save_to_db=save_to_db,
                    use_async=use_async
                )
            except Exception as e:
                error_msg = f"Failed to scrape {source}: {e}"
                logger.error(error_msg)
                self.results['errors'].append(error_msg)
        
        logger.info(
            f"Completed scraping all sources: "
            f"{self.results['total_scraped']} total scraped, "
            f"{self.results['total_saved']} total saved"
        )
        
        return self.results
    
    async def scrape_all_sources_async(
        self, 
        locations: List[str] = None, 
        max_pages: int = 10,
        save_to_db: bool = True,
        sources: List[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape apartments from all sources asynchronously.
        
        Args:
            locations: List of locations to scrape
            max_pages: Maximum pages to scrape per location
            save_to_db: Whether to save results to database
            sources: Specific sources to scrape (if None, scrape all)
            
        Returns:
            Dictionary with overall scraping results
        """
        # Reset results
        self.results = {
            'total_scraped': 0,
            'total_saved': 0,
            'by_source': {},
            'errors': []
        }
        
        # Determine which sources to scrape
        sources_to_scrape = sources if sources else list(self.scrapers.keys())
        
        logger.info(f"Starting async scraping from {len(sources_to_scrape)} sources: {sources_to_scrape}")
        
        # Create async tasks for each source
        tasks = []
        for source in sources_to_scrape:
            task = self._scrape_source_async(
                source=source,
                locations=locations,
                max_pages=max_pages,
                save_to_db=save_to_db
            )
            tasks.append(task)
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            source = sources_to_scrape[i]
            if isinstance(result, Exception):
                error_msg = f"Failed to scrape {source}: {result}"
                logger.error(error_msg)
                self.results['errors'].append(error_msg)
            else:
                self.results['total_scraped'] += result['scraped_count']
                self.results['total_saved'] += result['saved_count']
                self.results['by_source'][source] = result
        
        logger.info(
            f"Completed async scraping all sources: "
            f"{self.results['total_scraped']} total scraped, "
            f"{self.results['total_saved']} total saved"
        )
        
        return self.results
    
    async def _scrape_source_async(
        self,
        source: str,
        locations: List[str] = None,
        max_pages: int = 10,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """Async wrapper for scraping a single source."""
        try:
            scraper_class = self.scrapers[source]
            
            with scraper_class() as scraper:
                apartments = await scraper.scrape_all_async(locations, max_pages)
                
                saved_count = 0
                if save_to_db and apartments:
                    saved_count = self._save_apartments_to_db(apartments)
                
                logger.info(f"Async completed {source}: {len(apartments)} scraped, {saved_count} saved")
                
                return {
                    'source': source,
                    'scraped_count': len(apartments),
                    'saved_count': saved_count,
                    'apartments': apartments if not save_to_db else None
                }
        except Exception as e:
            logger.error(f"Async error scraping {source}: {e}")
            return {
                'source': source,
                'scraped_count': 0,
                'saved_count': 0,
                'error': str(e)
            }
    
    def _save_apartments_to_db(self, apartments: List[ApartmentCreate]) -> int:
        """Save apartments to database using upsert logic."""
        saved_count = 0
        
        try:
            # Get database session
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                for apartment in apartments:
                    try:
                        # Use upsert to avoid duplicates
                        result = ApartmentCRUD.upsert(db, apartment)
                        if result:
                            saved_count += 1
                    except Exception as e:
                        logger.error(f"Error saving apartment {apartment.title}: {e}")
                        continue
                
                logger.info(f"Saved {saved_count}/{len(apartments)} apartments to database")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Database error: {e}")
        
        return saved_count
    
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """Get current scraping statistics."""
        return self.results.copy()
    
    def reset_statistics(self):
        """Reset scraping statistics."""
        self.results = {
            'total_scraped': 0,
            'total_saved': 0,
            'by_source': {},
            'errors': []
        }
    
    def scrape_by_filters(
        self,
        locations: List[str] = None,
        max_pages: int = 10,
        sources: List[str] = None,
        save_to_db: bool = True,
        use_async: bool = False
    ) -> List[ApartmentCreate]:
        """
        Scrape apartments with specific filters and return raw data.
        
        Args:
            locations: List of locations to scrape
            max_pages: Maximum pages to scrape per location
            sources: Specific sources to scrape
            save_to_db: Whether to save to database
            use_async: Whether to use async scraping
            
        Returns:
            List of scraped apartments
        """
        all_apartments = []
        
        sources_to_scrape = sources if sources else list(self.scrapers.keys())
        
        for source in sources_to_scrape:
            try:
                result = self.scrape_source(
                    source=source,
                    locations=locations,
                    max_pages=max_pages,
                    save_to_db=save_to_db,
                    use_async=use_async
                )
                
                if 'apartments' in result and result['apartments']:
                    all_apartments.extend(result['apartments'])
                    
            except Exception as e:
                logger.error(f"Error scraping {source}: {e}")
                continue
        
        return all_apartments