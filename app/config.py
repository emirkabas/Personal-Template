"""
Configuration module for the apartment scraper application.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost:5432/apartment_scraper")
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
    
    # Scraping Configuration
    SCRAPE_INTERVAL_HOURS: int = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    REQUEST_DELAY_SECONDS: float = float(os.getenv("REQUEST_DELAY_SECONDS", "1"))
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "3600"))
    
    # Browser Configuration
    HEADLESS_BROWSER: bool = os.getenv("HEADLESS_BROWSER", "True").lower() == "true"
    BROWSER_TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "30"))
    
    # Proxy Configuration
    USE_PROXY: bool = os.getenv("USE_PROXY", "False").lower() == "true"
    PROXY_URL: Optional[str] = os.getenv("PROXY_URL")
    
    # User Agents for web scraping
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
    ]

# Global config instance
config = Config()