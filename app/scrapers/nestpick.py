"""
Nestpick apartment scraper.
"""
import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from loguru import logger
from app.models.apartment import ApartmentCreate
from .base import BaseScraper

class NestpickScraper(BaseScraper):
    """Scraper for Nestpick apartment listings."""
    
    def __init__(self):
        super().__init__("nestpick")
        self.base_url = "https://www.nestpick.com"
        self.search_urls = {
            "copenhagen": f"{self.base_url}/copenhagen/",
            "berlin": f"{self.base_url}/berlin/", 
            "barcelona": f"{self.base_url}/barcelona/",
            "amsterdam": f"{self.base_url}/amsterdam/",
            "": f"{self.base_url}/search/"  # General search
        }
    
    def get_listing_urls(self, location: str = "", max_pages: int = 10) -> List[str]:
        """Get URLs of individual apartment listings from Nestpick."""
        listing_urls = []
        
        # Get the search URL for the location
        search_url = self.search_urls.get(location.lower(), self.search_urls[""])
        
        try:
            for page in range(1, max_pages + 1):
                # Add pagination if needed
                page_url = f"{search_url}?page={page}" if page > 1 else search_url
                
                logger.debug(f"Scraping Nestpick page: {page_url}")
                soup = self.get_soup(page_url)
                
                # Find listing links
                # Based on the HTML structure observed, listings are in divs with apartment links
                listing_links = soup.find_all('a', href=True)
                
                page_listings = []
                for link in listing_links:
                    href = link.get('href', '')
                    
                    # Filter for apartment listing URLs
                    # Nestpick listing URLs typically contain property details
                    if any(indicator in href.lower() for indicator in ['/apartment/', '/studio/', '/room/', '/property/']):
                        full_url = urljoin(self.base_url, href)
                        if full_url not in listing_urls:
                            page_listings.append(full_url)
                
                if not page_listings:
                    logger.info(f"No more listings found on page {page}, stopping pagination")
                    break
                
                listing_urls.extend(page_listings)
                logger.debug(f"Found {len(page_listings)} listings on page {page}")
                
        except Exception as e:
            logger.error(f"Error getting listing URLs from Nestpick: {e}")
        
        return listing_urls
    
    def scrape_listing(self, url: str) -> Optional[ApartmentCreate]:
        """Scrape individual Nestpick apartment listing."""
        try:
            soup = self.get_soup(url, use_selenium=True)  # Use Selenium for JS-heavy pages
            
            # Extract apartment data based on Nestpick's structure
            apartment_data = {
                'source': self.source_name,
                'source_url': url,
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'address': self._extract_address(soup),
                'city': self._extract_city(soup, url),
                'price': self._extract_price(soup),
                'currency': self._extract_currency(soup),
                'size_sqm': self._extract_size(soup),
                'rooms': self._extract_rooms(soup),
                'bedrooms': self._extract_bedrooms(soup),
                'property_type': self._extract_property_type(soup, url),
                'furnished': self._extract_furnished(soup),
                'amenities': self._extract_amenities(soup),
                'images': self._extract_images(soup),
                'is_available': True
            }
            
            # Filter out None values and ensure required fields
            filtered_data = {k: v for k, v in apartment_data.items() if v is not None}
            
            # Ensure required fields are present
            if not filtered_data.get('title'):
                logger.warning(f"No title found for Nestpick listing: {url}")
                return None
            
            if not filtered_data.get('price') or filtered_data.get('price', 0) <= 0:
                logger.warning(f"No valid price found for Nestpick listing: {url}")
                return None
            
            if not filtered_data.get('city'):
                logger.warning(f"No city found for Nestpick listing: {url}")
                return None
            
            return ApartmentCreate(**filtered_data)
            
        except Exception as e:
            logger.error(f"Error scraping Nestpick listing {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract apartment title."""
        # Try multiple selectors for title
        selectors = [
            'h1',
            '.listing-title',
            '.property-title',
            '[data-testid="listing-title"]',
            'title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = self.clean_text(element.get_text())
                if title and len(title) > 5:  # Basic validation
                    return title
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract apartment description."""
        selectors = [
            '.listing-description',
            '.property-description',
            '.description',
            '[data-testid="description"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                description = self.clean_text(element.get_text())
                if description and len(description) > 20:
                    return description
        
        return None
    
    def _extract_address(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract apartment address."""
        selectors = [
            '.address',
            '.location',
            '.property-address',
            '[data-testid="address"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                address = self.clean_text(element.get_text())
                if address:
                    return address
        
        return None
    
    def _extract_city(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract city from various sources."""
        # First try to extract from page content
        selectors = [
            '.city',
            '.location-city',
            '[data-testid="city"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                city = self.clean_text(element.get_text())
                if city:
                    return city
        
        # Try to extract from URL
        url_parts = urlparse(url).path.split('/')
        for part in url_parts:
            if part.lower() in ['copenhagen', 'berlin', 'barcelona', 'amsterdam', 'madrid', 'paris']:
                return part.title()
        
        # Try breadcrumbs
        breadcrumb = soup.select_one('.breadcrumb')
        if breadcrumb:
            breadcrumb_text = breadcrumb.get_text()
            for city in ['Copenhagen', 'Berlin', 'Barcelona', 'Amsterdam', 'Madrid', 'Paris']:
                if city.lower() in breadcrumb_text.lower():
                    return city
        
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price."""
        selectors = [
            '.price',
            '.rent-price',
            '.monthly-price',
            '[data-testid="price"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text()
                price, _ = self.parse_currency(price_text)
                if price > 0:
                    return price
        
        # Try to find price in text content
        price_pattern = r'[€$£]\s*[\d,]+|\d+\s*[€$£kr]'
        text_content = soup.get_text()
        price_matches = re.findall(price_pattern, text_content)
        
        for match in price_matches:
            price, _ = self.parse_currency(match)
            if price > 100:  # Basic validation - price should be at least 100
                return price
        
        return None
    
    def _extract_currency(self, soup: BeautifulSoup) -> str:
        """Extract currency."""
        # Try to find currency in price elements
        selectors = [
            '.price',
            '.rent-price',
            '.monthly-price',
            '[data-testid="price"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text()
                _, currency = self.parse_currency(price_text)
                return currency
        
        return "EUR"  # Default for Nestpick
    
    def _extract_size(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract apartment size in square meters."""
        selectors = [
            '.size',
            '.area',
            '.sqm',
            '[data-testid="size"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                size_text = element.get_text()
                size = self.extract_number(size_text)
                if size and size > 10:  # Basic validation
                    return size
        
        # Try to find size in text content
        size_pattern = r'(\d+)\s*m[²2]|\b(\d+)\s*sqm\b'
        text_content = soup.get_text()
        size_matches = re.findall(size_pattern, text_content, re.IGNORECASE)
        
        for match in size_matches:
            size = self.extract_number(match[0] or match[1])
            if size and size > 10:
                return size
        
        return None
    
    def _extract_rooms(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract number of rooms."""
        selectors = [
            '.rooms',
            '.room-count',
            '[data-testid="rooms"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                rooms_text = element.get_text()
                rooms = self.extract_integer(rooms_text)
                if rooms and rooms > 0:
                    return rooms
        
        # Try to find rooms in text content
        room_pattern = r'(\d+)\s*room[s]?|\b(\d+)\s*bed'
        text_content = soup.get_text()
        room_matches = re.findall(room_pattern, text_content, re.IGNORECASE)
        
        for match in room_matches:
            rooms = self.extract_integer(match[0] or match[1])
            if rooms and rooms > 0:
                return rooms
        
        return None
    
    def _extract_bedrooms(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract number of bedrooms."""
        selectors = [
            '.bedrooms',
            '.bedroom-count',
            '[data-testid="bedrooms"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                bedrooms_text = element.get_text()
                bedrooms = self.extract_integer(bedrooms_text)
                if bedrooms and bedrooms > 0:
                    return bedrooms
        
        # Try to find bedrooms in text content
        bedroom_pattern = r'(\d+)\s*bedroom[s]?'
        text_content = soup.get_text()
        bedroom_matches = re.findall(bedroom_pattern, text_content, re.IGNORECASE)
        
        for match in bedroom_matches:
            bedrooms = self.extract_integer(match)
            if bedrooms and bedrooms > 0:
                return bedrooms
        
        return None
    
    def _extract_property_type(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract property type."""
        # Try to get from URL first
        if '/apartment/' in url.lower():
            return 'apartment'
        elif '/studio/' in url.lower():
            return 'studio'
        elif '/room/' in url.lower():
            return 'room'
        
        # Try to find in page content
        selectors = [
            '.property-type',
            '.listing-type',
            '[data-testid="property-type"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                prop_type = self.clean_text(element.get_text()).lower()
                if any(t in prop_type for t in ['apartment', 'studio', 'room', 'house']):
                    return prop_type
        
        return 'apartment'  # Default
    
    def _extract_furnished(self, soup: BeautifulSoup) -> Optional[bool]:
        """Extract furnished status."""
        text_content = soup.get_text().lower()
        
        # Look for furnished/unfurnished keywords
        if 'furnished' in text_content:
            if 'unfurnished' in text_content:
                return False
            return True
        
        return None
    
    def _extract_amenities(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract amenities list."""
        amenities = []
        
        # Try to find amenities section
        selectors = [
            '.amenities',
            '.features',
            '.facilities',
            '[data-testid="amenities"]'
        ]
        
        for selector in selectors:
            section = soup.select_one(selector)
            if section:
                amenity_items = section.find_all(['li', 'span', 'div'])
                for item in amenity_items:
                    amenity = self.clean_text(item.get_text())
                    if amenity and len(amenity) > 2:
                        amenities.append(amenity)
        
        return amenities if amenities else None
    
    def _extract_images(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract image URLs."""
        images = []
        
        # Find all image elements
        img_elements = soup.find_all('img', src=True)
        
        for img in img_elements:
            src = img.get('src', '')
            if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                # Make absolute URL
                full_url = urljoin(self.base_url, src)
                if full_url not in images:
                    images.append(full_url)
        
        return images if images else None