"""
Base scraper class with common functionality for all apartment website scrapers.
"""
import asyncio
import random
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import aiohttp
from loguru import logger
from app.config import config
from app.models.apartment import ApartmentCreate

class BaseScraper(ABC):
    """Base class for apartment website scrapers."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = None
        self.driver = None
        self.user_agent = random.choice(config.USER_AGENTS)
        
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        if self.session:
            self.session.close()
        if self.driver:
            self.driver.quit()
    
    def get_session(self) -> requests.Session:
        """Get or create a requests session."""
        if not self.session:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
        return self.session
    
    def get_driver(self) -> webdriver.Chrome:
        """Get or create a Selenium WebDriver."""
        if not self.driver:
            chrome_options = Options()
            chrome_options.add_argument(f'--user-agent={self.user_agent}')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if config.HEADLESS_BROWSER:
                chrome_options.add_argument('--headless')
            
            if config.USE_PROXY and config.PROXY_URL:
                chrome_options.add_argument(f'--proxy-server={config.PROXY_URL}')
            
            try:
                self.driver = webdriver.Chrome(
                    service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
                self.driver.set_page_load_timeout(config.BROWSER_TIMEOUT)
                # Execute script to prevent detection
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception as e:
                logger.error(f"Error creating WebDriver: {e}")
                raise
        
        return self.driver
    
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> requests.Response:
        """Make a request with error handling and rate limiting."""
        session = self.get_session()
        
        try:
            # Rate limiting
            time.sleep(config.REQUEST_DELAY_SECONDS)
            
            response = session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            
            logger.debug(f"Successfully fetched: {url}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
    
    def get_soup(self, url: str, use_selenium: bool = False) -> BeautifulSoup:
        """Get BeautifulSoup object from URL."""
        if use_selenium:
            driver = self.get_driver()
            try:
                driver.get(url)
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                html = driver.page_source
            except TimeoutException:
                logger.warning(f"Timeout loading page with Selenium: {url}")
                html = driver.page_source
            except WebDriverException as e:
                logger.error(f"WebDriver error for {url}: {e}")
                raise
        else:
            response = self.make_request(url)
            html = response.text
        
        return BeautifulSoup(html, 'html.parser')
    
    def extract_number(self, text: str) -> Optional[float]:
        """Extract number from text string."""
        if not text:
            return None
        
        import re
        # Remove any non-numeric characters except dots and commas
        cleaned = re.sub(r'[^\d.,]', '', text.replace(',', '.'))
        
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def extract_integer(self, text: str) -> Optional[int]:
        """Extract integer from text string."""
        number = self.extract_number(text)
        return int(number) if number is not None else None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        return ' '.join(text.strip().split())
    
    def parse_currency(self, price_text: str, default_currency: str = "DKK") -> tuple[float, str]:
        """Parse price and currency from text."""
        if not price_text:
            return 0.0, default_currency
        
        currency = default_currency
        
        # Common currency symbols and codes
        currency_patterns = {
            '€': 'EUR', 'EUR': 'EUR',
            '$': 'USD', 'USD': 'USD', 
            '£': 'GBP', 'GBP': 'GBP',
            'kr': 'DKK', 'DKK': 'DKK',
            'kr.': 'DKK', 'DKR': 'DKK'
        }
        
        for symbol, code in currency_patterns.items():
            if symbol.lower() in price_text.lower():
                currency = code
                break
        
        price = self.extract_number(price_text) or 0.0
        
        return price, currency
    
    @abstractmethod
    def get_listing_urls(self, location: str = "", max_pages: int = 10) -> List[str]:
        """Get URLs of individual apartment listings."""
        pass
    
    @abstractmethod
    def scrape_listing(self, url: str) -> Optional[ApartmentCreate]:
        """Scrape individual apartment listing."""
        pass
    
    def scrape_all(self, locations: List[str] = None, max_pages: int = 10) -> List[ApartmentCreate]:
        """Scrape all apartments from specified locations."""
        if not locations:
            locations = [""]  # Empty string for all locations
        
        all_apartments = []
        
        for location in locations:
            try:
                logger.info(f"Scraping {self.source_name} for location: {location or 'all'}")
                
                # Get listing URLs
                listing_urls = self.get_listing_urls(location, max_pages)
                logger.info(f"Found {len(listing_urls)} listings for {location or 'all'}")
                
                # Scrape each listing
                for i, url in enumerate(listing_urls, 1):
                    try:
                        logger.debug(f"Scraping listing {i}/{len(listing_urls)}: {url}")
                        apartment = self.scrape_listing(url)
                        
                        if apartment:
                            all_apartments.append(apartment)
                            logger.debug(f"Successfully scraped: {apartment.title}")
                        else:
                            logger.warning(f"No data extracted from: {url}")
                            
                    except Exception as e:
                        logger.error(f"Error scraping listing {url}: {e}")
                        continue
                    
                    # Rate limiting between requests
                    time.sleep(config.REQUEST_DELAY_SECONDS)
                
            except Exception as e:
                logger.error(f"Error scraping location {location}: {e}")
                continue
        
        logger.info(f"Scraped {len(all_apartments)} apartments from {self.source_name}")
        return all_apartments
    
    async def scrape_all_async(self, locations: List[str] = None, max_pages: int = 10) -> List[ApartmentCreate]:
        """Async version of scrape_all for better performance."""
        if not locations:
            locations = [""]
        
        all_apartments = []
        
        for location in locations:
            try:
                logger.info(f"Async scraping {self.source_name} for location: {location or 'all'}")
                
                # Get listing URLs (this should be made async in subclasses if needed)
                listing_urls = self.get_listing_urls(location, max_pages)
                logger.info(f"Found {len(listing_urls)} listings for {location or 'all'}")
                
                # Create semaphore to limit concurrent requests
                semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)
                
                # Create tasks for scraping listings
                tasks = [
                    self._scrape_listing_async(semaphore, url) 
                    for url in listing_urls
                ]
                
                # Execute tasks
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Async scraping error: {result}")
                    elif result:
                        all_apartments.append(result)
                
            except Exception as e:
                logger.error(f"Error in async scraping for location {location}: {e}")
                continue
        
        logger.info(f"Async scraped {len(all_apartments)} apartments from {self.source_name}")
        return all_apartments
    
    async def _scrape_listing_async(self, semaphore: asyncio.Semaphore, url: str) -> Optional[ApartmentCreate]:
        """Async wrapper for scraping individual listing."""
        async with semaphore:
            try:
                # Add delay for rate limiting
                await asyncio.sleep(config.REQUEST_DELAY_SECONDS)
                
                # Run the sync scrape_listing in executor
                loop = asyncio.get_event_loop()
                apartment = await loop.run_in_executor(None, self.scrape_listing, url)
                
                return apartment
            except Exception as e:
                logger.error(f"Error in async listing scraping {url}: {e}")
                return None