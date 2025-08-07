# Apartment Scraper

A comprehensive web scraping application that aggregates apartment listings from multiple Danish and European rental websites, providing a unified search interface with advanced filtering capabilities.

## 🌟 Features

- **Multi-Source Scraping**: Scrapes apartments from Nestpick, BoligZonen, and lejebolig.dk
- **Advanced Filtering**: Filter by location, price range, size, number of rooms, and amenities
- **REST API**: Full-featured API with pagination, sorting, and comprehensive search endpoints
- **Web Interface**: Beautiful Streamlit-based frontend for searching and managing scraping
- **Scheduled Scraping**: Automated periodic scraping to keep listings up-to-date
- **Analytics Dashboard**: Visualizations and statistics about apartment market trends
- **Database Storage**: PostgreSQL backend with proper indexing and relationships

## 🏗️ Architecture

```
├── app/
│   ├── api/              # FastAPI REST API
│   ├── database/         # Database models and CRUD operations
│   ├── frontend/         # Streamlit web interface
│   ├── models/           # Pydantic data models
│   ├── scrapers/         # Web scrapers for each source
│   └── utils/            # Utilities and scheduler
├── main.py               # Application launcher
├── requirements.txt      # Python dependencies
└── .env.example         # Environment variables template
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Google Chrome (for Selenium web scraping)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd apartment-scraper
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your database credentials and settings
```

4. **Initialize the database**
```bash
python main.py api --init-db
```

### Running the Application

#### Option 1: Full Application (API + Web Interface)
```bash
python main.py both
```
- API available at: http://localhost:8000
- Web interface at: http://localhost:8501
- API documentation: http://localhost:8000/docs

#### Option 2: API Server Only
```bash
python main.py api
```

#### Option 3: Web Interface Only
```bash
python main.py frontend
```

#### Option 4: One-time Scraping
```bash
python main.py scrape --sources nestpick boligzonen --locations copenhagen aarhus --max-pages 3
```

#### Option 5: Scheduled Scraping
```bash
python main.py schedule
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/apartment_scraper

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here

# Scraping Configuration
SCRAPE_INTERVAL_HOURS=6
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY_SECONDS=1

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Browser Configuration
HEADLESS_BROWSER=True
BROWSER_TIMEOUT=30
```

### Database Setup

The application uses PostgreSQL. Make sure you have a database created and update the `DATABASE_URL` in your `.env` file.

## 📊 API Endpoints

### Apartments
- `GET /api/v1/apartments` - Search and filter apartments
- `GET /api/v1/apartments/{id}` - Get specific apartment
- `GET /api/v1/apartments/cities` - Get available cities
- `GET /api/v1/apartments/stats` - Get apartment statistics
- `POST /api/v1/apartments` - Create apartment listing
- `PUT /api/v1/apartments/{id}` - Update apartment listing
- `DELETE /api/v1/apartments/{id}` - Delete apartment listing

### Scraping
- `GET /api/v1/scraping/sources` - Get available scraping sources
- `POST /api/v1/scraping/run` - Run scraping operation
- `POST /api/v1/scraping/run-async` - Run async scraping
- `GET /api/v1/scraping/stats` - Get scraping statistics
- `GET /api/v1/scraping/test/{source}` - Test individual scraper

### Health
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health status

## 🔍 Usage Examples

### Search Apartments via API

```bash
# Search apartments in Copenhagen under 15000 DKK
curl "http://localhost:8000/api/v1/apartments?city=Copenhagen&max_price=15000"

# Search furnished apartments with parking
curl "http://localhost:8000/api/v1/apartments?furnished=true&parking=true"

# Get apartments sorted by price
curl "http://localhost:8000/api/v1/apartments?sort_by=price&sort_order=asc"
```

### Run Scraping via API

```bash
# Start scraping all sources
curl -X POST "http://localhost:8000/api/v1/scraping/run" \
  -H "Content-Type: application/json" \
  -d '{"sources": ["nestpick", "boligzonen"], "locations": ["copenhagen"], "max_pages": 2}'

# Test a specific scraper
curl "http://localhost:8000/api/v1/scraping/test/nestpick"
```

## 🖥️ Web Interface Features

The Streamlit web interface provides:

1. **Apartment Search**: Advanced filtering with real-time results
2. **Scraping Management**: Control and monitor scraping operations
3. **Analytics Dashboard**: Market trends and statistics visualization
4. **API Status**: Health monitoring and quick statistics

### Web Interface Screenshots

The interface includes:
- Interactive filters for location, price, size, and amenities
- Real-time apartment cards with detailed information
- Scraping controls with progress monitoring
- Charts and analytics for market insights

## 🕐 Scheduled Scraping

The application includes a sophisticated scheduling system:

- **Daily Scraping**: Full scraping at 2 AM daily
- **Interval Scraping**: Quick updates every 6 hours
- **Custom Schedules**: Add your own cron-based schedules

### Managing Scheduled Jobs

```python
from app.utils.scheduler import apartment_scheduler

# Start the scheduler
apartment_scheduler.start()

# Add custom daily scraping
apartment_scheduler.add_daily_scraping(
    hour=14, minute=30,
    sources=['nestpick'],
    locations=['copenhagen'],
    max_pages=2
)

# List all jobs
jobs = apartment_scheduler.list_jobs()
```

## 🧪 Testing

### Test Individual Scrapers

```bash
# Test Nestpick scraper
python -c "
from app.scrapers.nestpick import NestpickScraper
with NestpickScraper() as scraper:
    urls = scraper.get_listing_urls('copenhagen', 1)
    print(f'Found {len(urls)} URLs')
"
```

### API Testing

Visit http://localhost:8000/docs for interactive API documentation and testing.

## 🗃️ Database Schema

The application uses a comprehensive database schema:

### Apartments Table
- Basic info: title, description, address, city
- Pricing: price, currency, deposit
- Property details: size, rooms, bedrooms, bathrooms
- Features: furnished, pets_allowed, balcony, parking, elevator
- Metadata: source, external_id, created_at, updated_at

### Indexes
- City, price, size, rooms for fast filtering
- Source and external_id for deduplication
- Active status for availability queries

## 🔒 Security Considerations

- Rate limiting implemented for API endpoints
- User-Agent rotation for web scraping
- Request delays to avoid overwhelming target websites
- Input validation and SQL injection prevention
- Environment variable based configuration

## 📈 Performance Optimization

- Async scraping for improved performance
- Database connection pooling
- Efficient pagination with proper indexing
- Selenium WebDriver management
- Request session reuse

## 🐛 Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
   - Ensure Chrome is installed
   - WebDriver is automatically managed via webdriver-manager

2. **Database Connection**
   - Verify PostgreSQL is running
   - Check DATABASE_URL format
   - Ensure database exists

3. **Import Errors**
   - Check all dependencies are installed
   - Verify Python path includes project root

4. **Scraping Failures**
   - Check internet connection
   - Verify target websites are accessible
   - Review rate limiting settings

### Logs

Application logs are stored in `logs/apartment_scraper.log` with rotation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

This project is for educational purposes. Please respect the target websites' robots.txt and terms of service.

## 🛣️ Roadmap

- [ ] Add more rental websites (Boliga, FindBolig, etc.)
- [ ] Implement user authentication and saved searches
- [ ] Add email notifications for new listings
- [ ] Implement map-based search
- [ ] Add price prediction models
- [ ] Mobile-responsive web interface
- [ ] Docker containerization
- [ ] Kubernetes deployment configurations

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Check API health endpoints
4. Create an issue with detailed information

---

**Note**: This scraper is designed to be respectful of target websites. It includes rate limiting, proper user agents, and delays between requests. Always review and comply with each website's robots.txt and terms of service.

