"""
BoligZonen apartment scraper for Danish rental properties.
"""
import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from loguru import logger
from app.models.apartment import ApartmentCreate
from .base import BaseScraper

class BoligZonenScraper(BaseScraper):
    """Scraper for BoligZonen apartment listings."""
    
    def __init__(self):
        super().__init__("boligzonen")
        self.base_url = "https://boligzonen.dk"
        self.search_urls = {
            "copenhagen": f"{self.base_url}/find-lejebolig/koebenhavn",
            "aarhus": f"{self.base_url}/find-lejebolig/aarhus",
            "odense": f"{self.base_url}/find-lejebolig/odense",
            "aalborg": f"{self.base_url}/find-lejebolig/aalborg",
            "": f"{self.base_url}/find-lejebolig"  # General search
        }
    
    def get_listing_urls(self, location: str = "", max_pages: int = 10) -> List[str]:
        """Get URLs of individual apartment listings from BoligZonen."""
        listing_urls = []
        
        # Get the search URL for the location
        search_url = self.search_urls.get(location.lower(), self.search_urls[""])
        
        try:
            for page in range(1, max_pages + 1):
                # Add pagination parameter
                page_url = f"{search_url}?side={page}" if page > 1 else search_url
                
                logger.debug(f"Scraping BoligZonen page: {page_url}")
                soup = self.get_soup(page_url)
                
                # Find listing links - BoligZonen uses specific patterns
                listing_links = soup.find_all('a', href=True)
                
                page_listings = []
                for link in listing_links:
                    href = link.get('href', '')
                    
                    # Filter for apartment listing URLs
                    # BoligZonen listing URLs typically contain 'bolig' and IDs
                    if ('/bolig/' in href.lower() or 
                        'lejebolig' in href.lower() or
                        re.search(r'/\d+/', href)):  # URLs with numeric IDs
                        
                        full_url = urljoin(self.base_url, href)
                        if full_url not in listing_urls:
                            page_listings.append(full_url)
                
                if not page_listings:
                    logger.info(f"No more listings found on page {page}, stopping pagination")
                    break
                
                listing_urls.extend(page_listings)
                logger.debug(f"Found {len(page_listings)} listings on page {page}")
                
        except Exception as e:
            logger.error(f"Error getting listing URLs from BoligZonen: {e}")
        
        return listing_urls
    
    def scrape_listing(self, url: str) -> Optional[ApartmentCreate]:
        """Scrape individual BoligZonen apartment listing."""
        try:
            soup = self.get_soup(url)
            
            # Extract apartment data based on BoligZonen's structure
            apartment_data = {
                'source': self.source_name,
                'source_url': url,
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'address': self._extract_address(soup),
                'city': self._extract_city(soup, url),
                'postal_code': self._extract_postal_code(soup),
                'price': self._extract_price(soup),
                'currency': 'DKK',  # BoligZonen is Danish, always DKK
                'size_sqm': self._extract_size(soup),
                'rooms': self._extract_rooms(soup),
                'property_type': self._extract_property_type(soup),
                'furnished': self._extract_furnished(soup),
                'pets_allowed': self._extract_pets_allowed(soup),
                'balcony': self._extract_balcony(soup),
                'parking': self._extract_parking(soup),
                'elevator': self._extract_elevator(soup),
                'amenities': self._extract_amenities(soup),
                'images': self._extract_images(soup),
                'contact_info': self._extract_contact_info(soup),
                'is_available': True,
                'country': 'Denmark'
            }
            
            # Filter out None values and ensure required fields
            filtered_data = {k: v for k, v in apartment_data.items() if v is not None}
            
            # Ensure required fields are present
            if not filtered_data.get('title'):
                logger.warning(f"No title found for BoligZonen listing: {url}")
                return None
            
            if not filtered_data.get('price') or filtered_data.get('price', 0) <= 0:
                logger.warning(f"No valid price found for BoligZonen listing: {url}")
                return None
            
            if not filtered_data.get('city'):
                logger.warning(f"No city found for BoligZonen listing: {url}")
                return None
            
            return ApartmentCreate(**filtered_data)
            
        except Exception as e:
            logger.error(f"Error scraping BoligZonen listing {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract apartment title."""
        selectors = [
            'h1',
            '.bolig-titel',
            '.property-title',
            '.listing-title',
            '.bolig-header h1',
            '.ad-title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = self.clean_text(element.get_text())
                if title and len(title) > 5:
                    return title
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract apartment description."""
        selectors = [
            '.bolig-beskrivelse',
            '.description',
            '.property-description',
            '.ad-description',
            '.beskrivelse'
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
            '.adresse',
            '.property-address',
            '.bolig-adresse',
            '.location'
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
        # Try to extract from page content
        selectors = [
            '.city',
            '.by',
            '.location-city',
            '.bolig-by'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                city = self.clean_text(element.get_text())
                if city:
                    return city
        
        # Try to extract from URL
        url_parts = urlparse(url).path.split('/')
        danish_cities = ['copenhagen', 'københavn', 'aarhus', 'odense', 'aalborg', 'esbjerg', 'randers', 'kolding', 'horsens', 'vejle']
        
        for part in url_parts:
            if part.lower() in danish_cities:
                # Map Danish names to English
                city_map = {
                    'københavn': 'Copenhagen',
                    'aarhus': 'Aarhus',
                    'odense': 'Odense',
                    'aalborg': 'Aalborg'
                }
                return city_map.get(part.lower(), part.title())
        
        # Try to extract from breadcrumbs or address
        address_text = soup.get_text()
        for city in danish_cities:
            if city.lower() in address_text.lower():
                return city.title()
        
        return None
    
    def _extract_postal_code(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract postal code."""
        # Danish postal codes are 4 digits
        text_content = soup.get_text()
        postal_pattern = r'\b(\d{4})\b'
        postal_matches = re.findall(postal_pattern, text_content)
        
        for match in postal_matches:
            # Basic validation for Danish postal codes (1000-9999)
            if 1000 <= int(match) <= 9999:
                return match
        
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price in DKK."""
        selectors = [
            '.price',
            '.pris',
            '.husleje',
            '.rent-price',
            '.bolig-pris',
            '.monthly-price'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text()
                price = self.extract_number(price_text)
                if price and price > 1000:  # Reasonable minimum for Danish rent
                    return price
        
        # Try to find price in text content with DKK patterns
        price_patterns = [
            r'(\d{1,3}(?:[.,]\d{3})*)\s*kr',
            r'(\d{1,3}(?:[.,]\d{3})*)\s*DKK',
            r'kr\s*(\d{1,3}(?:[.,]\d{3})*)',
            r'(\d{4,})\s*kr'
        ]
        
        text_content = soup.get_text()
        for pattern in price_patterns:
            price_matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in price_matches:
                price = self.extract_number(match)
                if price and price > 1000:
                    return price
        
        return None
    
    def _extract_size(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract apartment size in square meters."""
        selectors = [
            '.size',
            '.stoerrelse',
            '.area',
            '.kvadratmeter',
            '.m2',
            '.bolig-stoerrelse'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                size_text = element.get_text()
                size = self.extract_number(size_text)
                if size and size > 10:
                    return size
        
        # Try to find size in text content
        size_patterns = [
            r'(\d+)\s*m[²2]',
            r'(\d+)\s*kvadratmeter',
            r'(\d+)\s*kvm'
        ]
        
        text_content = soup.get_text()
        for pattern in size_patterns:
            size_matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in size_matches:
                size = self.extract_number(match)
                if size and size > 10:
                    return size
        
        return None
    
    def _extract_rooms(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract number of rooms."""
        selectors = [
            '.rooms',
            '.vaerelser',
            '.room-count',
            '.antal-vaerelser'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                rooms_text = element.get_text()
                rooms = self.extract_integer(rooms_text)
                if rooms and rooms > 0:
                    return rooms
        
        # Try to find rooms in text content
        room_patterns = [
            r'(\d+)\s*værelse[r]?',
            r'(\d+)\s*room[s]?',
            r'(\d+)\s*vær'
        ]
        
        text_content = soup.get_text()
        for pattern in room_patterns:
            room_matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in room_matches:
                rooms = self.extract_integer(match)
                if rooms and rooms > 0:
                    return rooms
        
        return None
    
    def _extract_property_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract property type."""
        selectors = [
            '.property-type',
            '.boligtype',
            '.type'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                prop_type = self.clean_text(element.get_text()).lower()
                
                # Map Danish terms to English
                type_mapping = {
                    'lejlighed': 'apartment',
                    'hus': 'house',
                    'værelse': 'room',
                    'studio': 'studio',
                    'rækkehus': 'townhouse',
                    'villa': 'house'
                }
                
                for danish, english in type_mapping.items():
                    if danish in prop_type:
                        return english
        
        # Try to find in text content
        text_content = soup.get_text().lower()
        if 'lejlighed' in text_content:
            return 'apartment'
        elif 'hus' in text_content:
            return 'house'
        elif 'værelse' in text_content:
            return 'room'
        
        return 'apartment'  # Default
    
    def _extract_furnished(self, soup: BeautifulSoup) -> Optional[bool]:
        """Extract furnished status."""
        text_content = soup.get_text().lower()
        
        # Look for Danish furnished keywords
        if any(word in text_content for word in ['møbleret', 'furnished', 'indrettet']):
            return True
        elif any(word in text_content for word in ['umøbleret', 'unfurnished']):
            return False
        
        return None
    
    def _extract_pets_allowed(self, soup: BeautifulSoup) -> Optional[bool]:
        """Extract pets allowed status."""
        text_content = soup.get_text().lower()
        
        # Look for Danish pet keywords
        if any(word in text_content for word in ['kæledyr tilladt', 'husdyr tilladt', 'pets allowed']):
            return True
        elif any(word in text_content for word in ['ingen kæledyr', 'no pets', 'kæledyr forbudt']):
            return False
        
        return None
    
    def _extract_balcony(self, soup: BeautifulSoup) -> Optional[bool]:
        """Extract balcony availability."""
        text_content = soup.get_text().lower()
        return 'altan' in text_content or 'balcony' in text_content or None
    
    def _extract_parking(self, soup: BeautifulSoup) -> Optional[bool]:
        """Extract parking availability."""
        text_content = soup.get_text().lower()
        return any(word in text_content for word in ['parkering', 'parking', 'garage', 'carport']) or None
    
    def _extract_elevator(self, soup: BeautifulSoup) -> Optional[bool]:
        """Extract elevator availability."""
        text_content = soup.get_text().lower()
        return 'elevator' in text_content or 'lift' in text_content or None
    
    def _extract_amenities(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract amenities list."""
        amenities = []
        
        selectors = [
            '.amenities',
            '.faciliteter',
            '.features',
            '.extras'
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
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> Optional[dict]:
        """Extract contact information."""
        contact_info = {}
        
        # Look for phone numbers
        phone_pattern = r'(\+45\s?)?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}'
        text_content = soup.get_text()
        phone_matches = re.findall(phone_pattern, text_content)
        if phone_matches:
            contact_info['phone'] = phone_matches[0]
        
        # Look for email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text_content)
        if email_matches:
            contact_info['email'] = email_matches[0]
        
        return contact_info if contact_info else None