"""
Streamlit web interface for apartment search and scraping management.
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Page configuration
st.set_page_config(
    page_title="Apartment Scraper Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    
    .filter-section {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    
    .apartment-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

def make_api_request(endpoint: str, method: str = "GET", params: dict = None, json_data: dict = None) -> Dict[Any, Any]:
    """Make API request with error handling."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, params=params, json=json_data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return {}
    except Exception as e:
        st.error(f"Error: {e}")
        return {}

def display_apartment_card(apartment: Dict[str, Any]):
    """Display an apartment as a card."""
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"### {apartment.get('title', 'No Title')}")
            st.write(f"📍 {apartment.get('address', 'No Address')}, {apartment.get('city', 'Unknown City')}")
            if apartment.get('description'):
                st.write(apartment['description'][:200] + "..." if len(apartment['description']) > 200 else apartment['description'])
        
        with col2:
            price = apartment.get('price', 0)
            currency = apartment.get('currency', 'DKK')
            st.metric("Price", f"{price:,.0f} {currency}")
            
            size = apartment.get('size_sqm')
            if size:
                st.metric("Size", f"{size} m²")
        
        with col3:
            rooms = apartment.get('rooms')
            if rooms:
                st.metric("Rooms", rooms)
            
            source = apartment.get('source', 'Unknown')
            st.write(f"Source: **{source.title()}**")
            
            if apartment.get('source_url'):
                st.markdown(f"[View Original]({apartment['source_url']})")
        
        st.divider()

def apartment_search_page():
    """Apartment search page."""
    st.markdown('<h1 class="main-header">🏠 Apartment Search</h1>', unsafe_allow_html=True)
    
    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Search Filters")
        
        # Location filters
        st.subheader("Location")
        city = st.selectbox("City", ["All", "Copenhagen", "Aarhus", "Odense", "Aalborg", "Berlin", "Barcelona"])
        
        # Price filters
        st.subheader("Price Range")
        col1, col2 = st.columns(2)
        with col1:
            min_price = st.number_input("Min Price", min_value=0, value=0, step=1000)
        with col2:
            max_price = st.number_input("Max Price", min_value=0, value=50000, step=1000)
        
        # Size filters
        st.subheader("Size (m²)")
        col1, col2 = st.columns(2)
        with col1:
            min_size = st.number_input("Min Size", min_value=0, value=0, step=10)
        with col2:
            max_size = st.number_input("Max Size", min_value=0, value=200, step=10)
        
        # Room filters
        st.subheader("Rooms")
        col1, col2 = st.columns(2)
        with col1:
            min_rooms = st.number_input("Min Rooms", min_value=0, value=0, step=1)
        with col2:
            max_rooms = st.number_input("Max Rooms", min_value=0, value=10, step=1)
        
        # Property features
        st.subheader("Features")
        furnished = st.selectbox("Furnished", ["Any", "Yes", "No"])
        pets_allowed = st.selectbox("Pets Allowed", ["Any", "Yes", "No"])
        balcony = st.selectbox("Balcony", ["Any", "Yes", "No"])
        parking = st.selectbox("Parking", ["Any", "Yes", "No"])
        elevator = st.selectbox("Elevator", ["Any", "Yes", "No"])
        
        # Source filter
        st.subheader("Source")
        source = st.selectbox("Source", ["All", "nestpick", "boligzonen", "lejebolig"])
        
        # Sorting
        st.subheader("Sorting")
        sort_by = st.selectbox("Sort by", ["created_at", "price", "size_sqm", "rooms"])
        sort_order = st.selectbox("Order", ["desc", "asc"])
        
        # Search button
        search_clicked = st.button("🔍 Search Apartments", type="primary")
    
    # Main content area
    if search_clicked or 'search_results' not in st.session_state:
        # Prepare search parameters
        params = {
            "page": 1,
            "page_size": 20,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "available_only": True
        }
        
        # Add optional filters
        if city != "All":
            params["city"] = city
        if min_price > 0:
            params["min_price"] = min_price
        if max_price > 0 and max_price != 50000:
            params["max_price"] = max_price
        if min_size > 0:
            params["min_size"] = min_size
        if max_size > 0 and max_size != 200:
            params["max_size"] = max_size
        if min_rooms > 0:
            params["min_rooms"] = min_rooms
        if max_rooms > 0 and max_rooms != 10:
            params["max_rooms"] = max_rooms
        if furnished != "Any":
            params["furnished"] = furnished == "Yes"
        if pets_allowed != "Any":
            params["pets_allowed"] = pets_allowed == "Yes"
        if balcony != "Any":
            params["balcony"] = balcony == "Yes"
        if parking != "Any":
            params["parking"] = parking == "Yes"
        if elevator != "Any":
            params["elevator"] = elevator == "Yes"
        if source != "All":
            params["source"] = source
        
        # Make API request
        with st.spinner("Searching apartments..."):
            results = make_api_request("/apartments", params=params)
        
        if results:
            st.session_state.search_results = results
    
    # Display results
    if 'search_results' in st.session_state and st.session_state.search_results:
        results = st.session_state.search_results
        apartments = results.get('apartments', [])
        pagination = results.get('pagination', {})
        
        # Results summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Results", pagination.get('total_items', 0))
        with col2:
            st.metric("Current Page", pagination.get('page', 1))
        with col3:
            st.metric("Total Pages", pagination.get('total_pages', 1))
        with col4:
            st.metric("Results/Page", len(apartments))
        
        # Display apartments
        if apartments:
            st.subheader(f"Found {len(apartments)} apartments")
            
            for apartment in apartments:
                display_apartment_card(apartment)
        else:
            st.info("No apartments found matching your criteria. Try adjusting your filters.")

def scraping_management_page():
    """Scraping management page."""
    st.markdown('<h1 class="main-header">🔧 Scraping Management</h1>', unsafe_allow_html=True)
    
    # Get available sources
    sources_data = make_api_request("/scraping/sources")
    available_sources = sources_data.get('sources', [])
    
    # Scraping controls
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🚀 Run Scraping")
        
        # Source selection
        selected_sources = st.multiselect(
            "Select Sources",
            available_sources,
            default=available_sources
        )
        
        # Location selection
        locations = st.multiselect(
            "Select Locations",
            ["copenhagen", "aarhus", "odense", "aalborg", "berlin", "barcelona"],
            default=["copenhagen"]
        )
        
        # Scraping parameters
        max_pages = st.slider("Max Pages per Location", 1, 10, 3)
        save_to_db = st.checkbox("Save to Database", value=True)
        use_async = st.checkbox("Use Async Scraping", value=False)
        
        # Run scraping button
        if st.button("🚀 Start Scraping", type="primary"):
            request_data = {
                "sources": selected_sources if selected_sources else None,
                "locations": locations if locations else None,
                "max_pages": max_pages,
                "save_to_db": save_to_db,
                "use_async": use_async
            }
            
            with st.spinner("Running scraping operation..."):
                if use_async:
                    results = make_api_request("/scraping/run-async", method="POST", json_data=request_data)
                else:
                    results = make_api_request("/scraping/run", method="POST", json_data=request_data)
            
            if results:
                st.success("Scraping completed!")
                st.json(results)
    
    with col2:
        st.subheader("📊 Scraping Statistics")
        
        # Get current stats
        stats_data = make_api_request("/scraping/stats")
        
        if stats_data:
            current_stats = stats_data.get('current_session_stats', {})
            
            # Display metrics
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.metric("Total Scraped", current_stats.get('total_scraped', 0))
            with col2_2:
                st.metric("Total Saved", current_stats.get('total_saved', 0))
            
            # Display by source
            by_source = current_stats.get('by_source', {})
            if by_source:
                st.subheader("Results by Source")
                source_df = pd.DataFrame([
                    {
                        'Source': source.title(),
                        'Scraped': data.get('scraped_count', 0),
                        'Saved': data.get('saved_count', 0)
                    }
                    for source, data in by_source.items()
                ])
                st.dataframe(source_df, use_container_width=True)
            
            # Display errors
            errors = current_stats.get('errors', [])
            if errors:
                st.subheader("⚠️ Errors")
                for error in errors:
                    st.error(error)
        
        # Reset stats button
        if st.button("🔄 Reset Statistics"):
            make_api_request("/scraping/reset-stats", method="POST")
            st.success("Statistics reset!")
            st.rerun()
    
    # Test individual scrapers
    st.subheader("🧪 Test Scrapers")
    
    col1, col2, col3 = st.columns(3)
    
    for i, source in enumerate(available_sources):
        with [col1, col2, col3][i % 3]:
            if st.button(f"Test {source.title()}", key=f"test_{source}"):
                with st.spinner(f"Testing {source}..."):
                    test_results = make_api_request(f"/scraping/test/{source}")
                
                if test_results:
                    status = test_results.get('status', 'unknown')
                    if status == 'success':
                        st.success(f"{source} test successful!")
                    else:
                        st.warning(f"{source} test completed with no results")
                    
                    with st.expander(f"View {source} test details"):
                        st.json(test_results)

def analytics_page():
    """Analytics and statistics page."""
    st.markdown('<h1 class="main-header">📊 Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    # Get apartment statistics
    stats_data = make_api_request("/apartments/stats")
    
    if stats_data:
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Apartments", stats_data.get('total_apartments', 0))
        with col2:
            st.metric("Active Apartments", stats_data.get('active_apartments', 0))
        with col3:
            avg_price = stats_data.get('average_price', 0)
            st.metric("Average Price", f"{avg_price:,.0f} DKK")
        with col4:
            min_price = stats_data.get('min_price', 0)
            max_price = stats_data.get('max_price', 0)
            st.metric("Price Range", f"{min_price:,.0f} - {max_price:,.0f}")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Apartments by source
            by_source = stats_data.get('by_source', {})
            if by_source:
                st.subheader("Apartments by Source")
                
                source_df = pd.DataFrame([
                    {'Source': source.title(), 'Count': count}
                    for source, count in by_source.items()
                ])
                
                fig = px.pie(source_df, values='Count', names='Source', 
                           title="Distribution by Source")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top cities
            top_cities = stats_data.get('top_cities', {})
            if top_cities:
                st.subheader("Top Cities")
                
                cities_df = pd.DataFrame([
                    {'City': city, 'Count': count}
                    for city, count in list(top_cities.items())[:10]
                ])
                
                fig = px.bar(cities_df, x='City', y='Count', 
                           title="Apartments by City")
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        
        # Get cities for detailed analysis
        cities_data = make_api_request("/apartments/cities")
        if cities_data:
            st.subheader("🏙️ City Analysis")
            
            selected_city = st.selectbox("Select city for detailed analysis", cities_data)
            
            if selected_city:
                # Get apartments for selected city
                city_params = {
                    "city": selected_city,
                    "page_size": 100,
                    "available_only": True
                }
                
                city_apartments = make_api_request("/apartments", params=city_params)
                
                if city_apartments and city_apartments.get('apartments'):
                    apartments = city_apartments['apartments']
                    
                    # Convert to DataFrame for analysis
                    df = pd.DataFrame(apartments)
                    
                    # Price distribution
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if 'price' in df.columns:
                            fig = px.histogram(df, x='price', nbins=20, 
                                             title=f"Price Distribution in {selected_city}")
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        if 'size_sqm' in df.columns:
                            fig = px.histogram(df, x='size_sqm', nbins=20,
                                             title=f"Size Distribution in {selected_city}")
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Price vs Size scatter plot
                    if 'price' in df.columns and 'size_sqm' in df.columns:
                        df_clean = df.dropna(subset=['price', 'size_sqm'])
                        if not df_clean.empty:
                            fig = px.scatter(df_clean, x='size_sqm', y='price', 
                                           color='source', title=f"Price vs Size in {selected_city}")
                            st.plotly_chart(fig, use_container_width=True)

def main():
    """Main application."""
    # Sidebar navigation
    with st.sidebar:
        st.title("🏠 Apartment Scraper")
        
        # Navigation
        page = st.radio(
            "Navigate to:",
            ["🔍 Search Apartments", "🔧 Scraping Management", "📊 Analytics"],
            key="navigation"
        )
        
        st.divider()
        
        # API Status
        st.subheader("🔗 API Status")
        try:
            health_check = make_api_request("/health")
            if health_check.get('status') == 'healthy':
                st.success("API is healthy")
            else:
                st.error("API is not responding")
        except:
            st.error("Cannot connect to API")
        
        st.divider()
        
        # Quick stats
        st.subheader("📋 Quick Stats")
        try:
            stats = make_api_request("/apartments/stats")
            if stats:
                st.metric("Total Apartments", stats.get('total_apartments', 0))
                st.metric("Active Listings", stats.get('active_apartments', 0))
        except:
            st.error("Cannot load stats")
    
    # Main content based on navigation
    if "Search Apartments" in page:
        apartment_search_page()
    elif "Scraping Management" in page:
        scraping_management_page()
    elif "Analytics" in page:
        analytics_page()

if __name__ == "__main__":
    main()