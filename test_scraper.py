#!/usr/bin/env python
"""
Test script to scrape a specific Craigslist car listing URL and print the extracted data.
"""

import os
import sys
import json
from urllib.parse import urlparse

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the scraper
from carDataScraper.scraper.utils.scraper import CraigslistScraper

def test_scrape_listing(url):
    """
    Scrape a specific listing URL and print the extracted data.
    """
    print(f"Testing scraper with URL: {url}")
    
    # Create a scraper instance
    scraper = CraigslistScraper()
    
    # Extract the domain from the URL
    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split('.')
    domain = domain_parts[0] if domain_parts else ''
    
    # Scrape the listing details
    details = scraper._scrape_listing_details(url)
    
    # Print the extracted data
    print("\nExtracted Data:")
    print(f"State: {details.get('state', '')}")
    print(f"City: {details.get('city', '')}")
    
    # Get the title from the URL path (better than using the listing ID)
    path_parts = parsed_url.path.split('/')
    if len(path_parts) > 5:
        # Extract from URL path (e.g., /lynbrook-2012-volkswagen-eos-2dr-conv/)
        title_part = path_parts[4]
        title = title_part.replace('-', ' ').title() if title_part else 'Unknown Title'
    else:
        title = 'Unknown Title'
    print(f"Title: {title}")
    
    # Also print the price if available
    price_match = None
    description = details.get('description', '')
    import re
    price_match = re.search(r'\$(\d+,?\d*)', description)
    price = price_match.group(0) if price_match else 'Not found'
    print(f"Price: {price}")
    
    print(f"Description: {details.get('description', '')[:200]}...")  # Print first 200 chars
    print(f"Phone Number: {details.get('phone_number', 'Not found')}")
    
    # Print photo URLs
    photo_urls = details.get('photo_urls', [])
    print(f"\nFound {len(photo_urls)} photos:")
    for i, url in enumerate(photo_urls[:5]):  # Print first 5 photo URLs
        print(f"  Photo {i+1}: {url}")
    
    if len(photo_urls) > 5:
        print(f"  ... and {len(photo_urls) - 5} more photos")
    
    # Return the details for further processing if needed
    return details

if __name__ == "__main__":
    # Use the provided URL or a default one
    url = sys.argv[1] if len(sys.argv) > 1 else "https://newyork.craigslist.org/lgi/ctd/d/lynbrook-2012-volkswagen-eos-2dr-conv/7835765436.html"
    
    # Test the scraper
    test_scrape_listing(url)
