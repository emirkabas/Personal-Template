#!/usr/bin/env python3
"""
Main launcher script for the Apartment Scraper application.

This script provides different ways to run the application:
- API server only
- Streamlit frontend only  
- Both API and frontend
- One-time scraping
- Scheduled scraping
"""
import argparse
import asyncio
import sys
import uvicorn
import subprocess
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import config
from app.database.session import init_db
from app.scrapers.manager import ScraperManager
from app.utils.scheduler import apartment_scheduler
from loguru import logger

def setup_logging():
    """Configure logging."""
    logger.remove()  # Remove default logger
    logger.add(
        sys.stderr,
        level=config.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Also log to file
    logger.add(
        "logs/apartment_scraper.log",
        rotation="1 day",
        retention="30 days",
        level=config.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

def run_api_server():
    """Run the FastAPI server."""
    logger.info("Starting FastAPI server...")
    uvicorn.run(
        "app.api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )

def run_streamlit_frontend():
    """Run the Streamlit frontend."""
    logger.info("Starting Streamlit frontend...")
    
    # Change to the correct directory and run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "app/frontend/streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])

def run_both():
    """Run both API server and Streamlit frontend."""
    import threading
    import time
    
    logger.info("Starting both API server and Streamlit frontend...")
    
    # Start API server in a separate thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # Wait a moment for API to start
    time.sleep(3)
    
    # Start Streamlit frontend (blocking)
    run_streamlit_frontend()

async def run_scraping(sources=None, locations=None, max_pages=5):
    """Run one-time scraping."""
    logger.info("Running one-time scraping...")
    
    # Initialize database
    init_db()
    
    # Create scraper manager
    scraper_manager = ScraperManager()
    
    # Run scraping
    results = await scraper_manager.scrape_all_sources_async(
        sources=sources,
        locations=locations,
        max_pages=max_pages,
        save_to_db=True
    )
    
    logger.info(f"Scraping completed: {results}")
    return results

async def run_scheduler():
    """Run the scheduler for periodic scraping."""
    logger.info("Starting apartment scraping scheduler...")
    
    # Initialize database
    init_db()
    
    # Start scheduler
    apartment_scheduler.start()
    
    try:
        # Keep the scheduler running
        while True:
            await asyncio.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler...")
        apartment_scheduler.stop()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Apartment Scraper Application")
    parser.add_argument(
        "mode",
        choices=["api", "frontend", "both", "scrape", "schedule"],
        help="Application mode"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=["nestpick", "boligzonen", "lejebolig"],
        help="Sources to scrape (for scrape mode)"
    )
    parser.add_argument(
        "--locations",
        nargs="+",
        help="Locations to scrape (for scrape mode)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum pages to scrape per location"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database before running"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Initialize database if requested
    if args.init_db or args.mode in ["scrape", "schedule"]:
        logger.info("Initializing database...")
        init_db()
    
    # Run based on mode
    if args.mode == "api":
        run_api_server()
    
    elif args.mode == "frontend":
        run_streamlit_frontend()
    
    elif args.mode == "both":
        run_both()
    
    elif args.mode == "scrape":
        asyncio.run(run_scraping(
            sources=args.sources,
            locations=args.locations,
            max_pages=args.max_pages
        ))
    
    elif args.mode == "schedule":
        asyncio.run(run_scheduler())

if __name__ == "__main__":
    main()