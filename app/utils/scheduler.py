"""
Scheduler for periodic apartment scraping operations.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.config import config
from app.scrapers.manager import ScraperManager

class ApartmentScrapingScheduler:
    """Scheduler for automated apartment scraping."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scraper_manager = ScraperManager()
        self.is_running = False
        
        # Default scraping configuration
        self.default_config = {
            'sources': ['nestpick', 'boligzonen', 'lejebolig'],
            'locations': ['copenhagen', 'aarhus', 'odense'],
            'max_pages': 3,
            'save_to_db': True
        }
    
    def start(self):
        """Start the scheduler."""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Apartment scraping scheduler started")
            
            # Add default jobs
            self._add_default_jobs()
    
    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Apartment scraping scheduler stopped")
    
    def _add_default_jobs(self):
        """Add default scraping jobs based on configuration."""
        # Daily full scraping at 2 AM
        self.add_daily_scraping(
            hour=2,
            minute=0,
            sources=self.default_config['sources'],
            locations=self.default_config['locations'],
            max_pages=self.default_config['max_pages']
        )
        
        # Hourly quick scraping during business hours
        self.add_interval_scraping(
            hours=config.SCRAPE_INTERVAL_HOURS,
            sources=self.default_config['sources'],
            locations=['copenhagen'],  # Quick scrape just Copenhagen
            max_pages=1
        )
    
    def add_daily_scraping(
        self,
        hour: int = 2,
        minute: int = 0,
        sources: List[str] = None,
        locations: List[str] = None,
        max_pages: int = 5,
        job_id: str = None
    ):
        """
        Add a daily scraping job.
        
        Args:
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            sources: List of sources to scrape
            locations: List of locations to scrape
            max_pages: Max pages per location
            job_id: Unique job identifier
        """
        if not job_id:
            job_id = f"daily_scraping_{hour:02d}_{minute:02d}"
        
        sources = sources or self.default_config['sources']
        locations = locations or self.default_config['locations']
        
        trigger = CronTrigger(hour=hour, minute=minute)
        
        self.scheduler.add_job(
            func=self._run_scheduled_scraping,
            trigger=trigger,
            args=[sources, locations, max_pages],
            id=job_id,
            name=f"Daily scraping at {hour:02d}:{minute:02d}",
            replace_existing=True
        )
        
        logger.info(f"Added daily scraping job: {job_id} at {hour:02d}:{minute:02d}")
    
    def add_interval_scraping(
        self,
        hours: int = None,
        minutes: int = None,
        sources: List[str] = None,
        locations: List[str] = None,
        max_pages: int = 3,
        job_id: str = None
    ):
        """
        Add an interval-based scraping job.
        
        Args:
            hours: Interval in hours
            minutes: Interval in minutes
            sources: List of sources to scrape
            locations: List of locations to scrape
            max_pages: Max pages per location
            job_id: Unique job identifier
        """
        if not hours and not minutes:
            hours = config.SCRAPE_INTERVAL_HOURS
        
        if not job_id:
            interval_str = f"{hours}h" if hours else f"{minutes}m"
            job_id = f"interval_scraping_{interval_str}"
        
        sources = sources or self.default_config['sources']
        locations = locations or self.default_config['locations']
        
        trigger = IntervalTrigger(hours=hours, minutes=minutes)
        
        self.scheduler.add_job(
            func=self._run_scheduled_scraping,
            trigger=trigger,
            args=[sources, locations, max_pages],
            id=job_id,
            name=f"Interval scraping every {hours or 0}h {minutes or 0}m",
            replace_existing=True
        )
        
        logger.info(f"Added interval scraping job: {job_id}")
    
    def add_weekly_scraping(
        self,
        day_of_week: int,
        hour: int = 2,
        minute: int = 0,
        sources: List[str] = None,
        locations: List[str] = None,
        max_pages: int = 10,
        job_id: str = None
    ):
        """
        Add a weekly scraping job.
        
        Args:
            day_of_week: Day of week (0=Monday, 6=Sunday)
            hour: Hour to run
            minute: Minute to run
            sources: List of sources to scrape
            locations: List of locations to scrape
            max_pages: Max pages per location
            job_id: Unique job identifier
        """
        if not job_id:
            days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            job_id = f"weekly_scraping_{days[day_of_week]}_{hour:02d}_{minute:02d}"
        
        sources = sources or self.default_config['sources']
        locations = locations or self.default_config['locations']
        
        trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        
        self.scheduler.add_job(
            func=self._run_scheduled_scraping,
            trigger=trigger,
            args=[sources, locations, max_pages],
            id=job_id,
            name=f"Weekly scraping on day {day_of_week} at {hour:02d}:{minute:02d}",
            replace_existing=True
        )
        
        logger.info(f"Added weekly scraping job: {job_id}")
    
    async def _run_scheduled_scraping(
        self,
        sources: List[str],
        locations: List[str],
        max_pages: int
    ):
        """Run scheduled scraping operation."""
        try:
            logger.info(f"Starting scheduled scraping: sources={sources}, locations={locations}, max_pages={max_pages}")
            
            start_time = datetime.now()
            
            # Run async scraping
            results = await self.scraper_manager.scrape_all_sources_async(
                sources=sources,
                locations=locations,
                max_pages=max_pages,
                save_to_db=True
            )
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(
                f"Scheduled scraping completed in {duration.total_seconds():.1f}s: "
                f"scraped={results.get('total_scraped', 0)}, "
                f"saved={results.get('total_saved', 0)}"
            )
            
            # Log any errors
            errors = results.get('errors', [])
            if errors:
                logger.warning(f"Scheduled scraping had {len(errors)} errors: {errors}")
            
        except Exception as e:
            logger.error(f"Error in scheduled scraping: {e}")
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed scheduled job: {job_id}")
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
    
    def list_jobs(self) -> List[dict]:
        """List all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def pause_job(self, job_id: str):
        """Pause a scheduled job."""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
    
    def resume_job(self, job_id: str):
        """Resume a paused job."""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
    
    def modify_job(
        self,
        job_id: str,
        sources: List[str] = None,
        locations: List[str] = None,
        max_pages: int = None,
        **trigger_kwargs
    ):
        """Modify an existing job."""
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            # Update job arguments if provided
            new_args = list(job.args)
            if sources is not None:
                new_args[0] = sources
            if locations is not None:
                new_args[1] = locations
            if max_pages is not None:
                new_args[2] = max_pages
            
            # Update trigger if provided
            if trigger_kwargs:
                self.scheduler.modify_job(job_id, args=new_args, **trigger_kwargs)
            else:
                self.scheduler.modify_job(job_id, args=new_args)
            
            logger.info(f"Modified job: {job_id}")
            
        except Exception as e:
            logger.error(f"Error modifying job {job_id}: {e}")
    
    def run_job_now(self, job_id: str):
        """Run a scheduled job immediately."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                # Run the job function directly
                asyncio.create_task(job.func(*job.args))
                logger.info(f"Triggered immediate run of job: {job_id}")
            else:
                logger.error(f"Job {job_id} not found")
        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}")
    
    def get_next_run_times(self, limit: int = 10) -> List[dict]:
        """Get next run times for all jobs."""
        next_runs = []
        
        for job in self.scheduler.get_jobs():
            if job.next_run_time:
                next_runs.append({
                    'job_id': job.id,
                    'job_name': job.name,
                    'next_run_time': job.next_run_time.isoformat(),
                    'trigger': str(job.trigger)
                })
        
        # Sort by next run time
        next_runs.sort(key=lambda x: x['next_run_time'])
        
        return next_runs[:limit]

# Global scheduler instance
apartment_scheduler = ApartmentScrapingScheduler()