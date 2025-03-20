#!/usr/bin/env python
"""
Test script to scrape multiple Craigslist car listings and print the extracted data.
This helps verify that our scraper works correctly for different types of listings.
"""

import os
import sys
import json
import random
from urllib.parse import urlparse

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the scraper
from carDataScraper.scraper.utils.scraper import CraigslistScraper

def test_scrape_city(city_domain, max_listings=3):
    """
    Scrape a specific city and print details for a few random listings.
    """
    print(f"Testing scraper with city: {city_domain}")
    
    # Create a scraper instance
    scraper = CraigslistScraper()
    
    # Scrape the city
    result = scraper.scrape_city(city_domain)
    
    if not result['success']:
        print(f"Error scraping {city_domain}: {result.get('error', 'Unknown error')}")
        return
    
    listings = result['listings']
    print(f"Found {len(listings)} listings in {city_domain}")
    
    if not listings:
        print("No listings found.")
        return
    
    # Select a few random listings to test
    sample_size = min(max_listings, len(listings))
    sample_listings = random.sample(listings, sample_size)
    
    # Print details for each sample listing
    for i, listing in enumerate(sample_listings):
        print(f"\n--- Listing {i+1} ---")
        print(f"Title: {listing.get('title', 'N/A')}")
        print(f"Price: {listing.get('price', 'N/A')}")
        print(f"State: {listing.get('state', 'N/A')}")
        print(f"City: {listing.get('city', 'N/A')}")
        print(f"Phone Number: {listing.get('phone_number', 'N/A')}")
        
        # Print a snippet of the description
        description = listing.get('description', '')
        if description:
            print(f"Description: {description[:150]}...")
        else:
            print("Description: N/A")
        
        # Print photo URLs
        photo_urls = listing.get('photo_urls', [])
        print(f"Photos: {len(photo_urls)} found")
        for j, url in enumerate(photo_urls[:3]):  # Print first 3 photo URLs
            print(f"  Photo {j+1}: {url}")
        
        if len(photo_urls) > 3:
            print(f"  ... and {len(photo_urls) - 3} more photos")

def test_specific_listing(url):
    """
    Test scraping a specific listing URL.
    """
    print(f"Testing specific listing: {url}")
    
    # Create a scraper instance
    scraper = CraigslistScraper()
    
    # Scrape the listing details
    details = scraper._scrape_listing_details(url)
    
    # Print the extracted data
    print("\nExtracted Data:")
    print(f"State: {details.get('state', 'N/A')}")
    print(f"City: {details.get('city', 'N/A')}")
    
    # Get the title from the URL path
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    if len(path_parts) > 4:
        title_part = path_parts[4]
        title = title_part.replace('-', ' ').title() if title_part else 'Unknown Title'
    else:
        title = 'Unknown Title'
    print(f"Title: {title}")
    
    # Extract price from description
    import re
    description = details.get('description', '')
    price_match = re.search(r'\$(\d+,?\d*)', description)
    price = price_match.group(0) if price_match else 'Not found'
    print(f"Price: {price}")
    
    print(f"Description: {description[:200]}...")  # Print first 200 chars
    print(f"Phone Number: {details.get('phone_number', 'Not found')}")
    
    # Print photo URLs
    photo_urls = details.get('photo_urls', [])
    print(f"\nFound {len(photo_urls)} photos:")
    for i, url in enumerate(photo_urls[:5]):  # Print first 5 photo URLs
        print(f"  Photo {i+1}: {url}")
    
    if len(photo_urls) > 5:
        print(f"  ... and {len(photo_urls) - 5} more photos")

if __name__ == "__main__":
    # Test specific listing if URL provided
    if len(sys.argv) > 1 and sys.argv[1].startswith('http'):
        test_specific_listing(sys.argv[1])
    else:
        # Test a few cities
        cities_to_test = ['newyork', 'losangeles', 'chicago', 'sfbay']
        city = sys.argv[1] if len(sys.argv) > 1 else random.choice(cities_to_test)
        test_scrape_city(city)
