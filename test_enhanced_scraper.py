#!/usr/bin/env python
"""
Test script for the enhanced Craigslist car data scraper.
This script tests the scraper with a limited number of cities and listings.
"""

import os
import sys
import json
import logging
from enhanced_scraper import EnhancedCraigslistScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_collect_links(city_domains=None, max_cities=3):
    """
    Test collecting car links from a few cities
    
    Args:
        city_domains (list): List of city domains to test (e.g., ['newyork', 'chicago'])
        max_cities (int): Maximum number of cities to test if city_domains is None
    """
    logger.info("Testing link collection...")
    
    # Create a scraper instance
    scraper = EnhancedCraigslistScraper()
    
    # Get the list of cities to test
    if city_domains is None:
        all_cities = scraper.get_cities()
        cities_to_test = all_cities[:max_cities]
        city_domains = [city['domain'] for city in cities_to_test]
    
    # Collect links for each city
    for city_domain in city_domains:
        logger.info(f"Collecting links for {city_domain}...")
        result = scraper.collect_car_links(city_domain)
        
        links = result['links']
        logger.info(f"Found {len(links)} links for {city_domain}")
        
        # Print a few sample links
        for i, link in enumerate(links[:5]):
            logger.info(f"  Link {i+1}: {link}")
        
        if len(links) > 5:
            logger.info(f"  ... and {len(links) - 5} more links")
    
    logger.info("Link collection test completed")

def test_scrape_details(city_domains=None, max_cities=2, max_links_per_city=3):
    """
    Test scraping car details from a few cities and a limited number of links
    
    Args:
        city_domains (list): List of city domains to test (e.g., ['newyork', 'chicago'])
        max_cities (int): Maximum number of cities to test if city_domains is None
        max_links_per_city (int): Maximum number of links to scrape per city
    """
    logger.info("Testing car details scraping...")
    
    # Create a scraper instance
    scraper = EnhancedCraigslistScraper()
    
    # Get the list of cities to test
    if city_domains is None:
        all_cities = scraper.get_cities()
        cities_to_test = all_cities[:max_cities]
        city_domains = [city['domain'] for city in cities_to_test]
    
    # Collect links and scrape details for each city
    for city_domain in city_domains:
        logger.info(f"Testing {city_domain}...")
        
        # Collect links
        result = scraper.collect_car_links(city_domain)
        links = result['links']
        
        if not links:
            logger.warning(f"No links found for {city_domain}")
            continue
        
        # Limit the number of links to scrape
        links_to_scrape = links[:max_links_per_city]
        logger.info(f"Scraping {len(links_to_scrape)} out of {len(links)} links for {city_domain}")
        
        # Scrape details for each link
        for link in links_to_scrape:
            logger.info(f"Scraping details for {link}")
            car_details = scraper.scrape_car_details(link)
            
            if 'error' in car_details:
                logger.error(f"Error scraping {link}: {car_details['error']}")
                continue
            
            # Print the car details
            logger.info(f"Title: {car_details.get('title', 'N/A')}")
            logger.info(f"Price: {car_details.get('price', 'N/A')}")
            logger.info(f"Location: {car_details.get('location', 'N/A')}")
            logger.info(f"State: {car_details.get('state', 'N/A')}")
            logger.info(f"City: {car_details.get('city', 'N/A')}")
            logger.info(f"Phone Number: {car_details.get('phone_number', 'N/A')}")
            
            # Print a snippet of the description
            description = car_details.get('description', '')
            if description:
                logger.info(f"Description: {description[:150]}...")
            else:
                logger.info("Description: N/A")
            
            # Print photo URLs
            photo_urls = car_details.get('photo_urls', [])
            logger.info(f"Photos: {len(photo_urls)} found")
            for i, url in enumerate(photo_urls[:3]):  # Print first 3 photo URLs
                logger.info(f"  Photo {i+1}: {url}")
            
            if len(photo_urls) > 3:
                logger.info(f"  ... and {len(photo_urls) - 3} more photos")
            
            # Print attributes
            attributes = car_details.get('attributes', {})
            if attributes:
                logger.info("Attributes:")
                for key, value in attributes.items():
                    logger.info(f"  {key}: {value}")
            
            logger.info("-" * 50)
    
    logger.info("Car details scraping test completed")

def test_full_scrape(city_domains=None, max_cities=2, max_links_per_city=5):
    """
    Test the full scraping process with a limited number of cities and links
    
    Args:
        city_domains (list): List of city domains to test (e.g., ['newyork', 'chicago'])
        max_cities (int): Maximum number of cities to test if city_domains is None
        max_links_per_city (int): Maximum number of links to scrape per city
    """
    logger.info("Testing full scraping process...")
    
    # Create a scraper instance
    scraper = EnhancedCraigslistScraper()
    
    # Get the list of cities to test
    if city_domains is None:
        all_cities = scraper.get_cities()
        cities_to_test = all_cities[:max_cities]
        city_domains = [city['domain'] for city in cities_to_test]
    
    # Phase 1: Collect all car links from each city
    all_links_by_city = {}
    
    for city_domain in city_domains:
        logger.info(f"Collecting links for {city_domain}...")
        result = scraper.collect_car_links(city_domain)
        
        links = result['links']
        logger.info(f"Found {len(links)} links for {city_domain}")
        
        # Limit the number of links to scrape
        links_to_scrape = links[:max_links_per_city]
        all_links_by_city[city_domain] = links_to_scrape
    
    # Phase 2: Visit each link to get detailed information
    all_cars_by_city = {}
    
    for city_domain, links in all_links_by_city.items():
        logger.info(f"Scraping {len(links)} car details for {city_domain}")
        
        car_details_list = []
        
        for link in links:
            logger.info(f"Scraping details for {link}")
            car_details = scraper.scrape_car_details(link)
            
            if 'error' not in car_details:
                car_details_list.append(car_details)
        
        all_cars_by_city[city_domain] = car_details_list
        
        logger.info(f"Scraped {len(car_details_list)} car details for {city_domain}")
    
    # Format the results
    formatted_results = scraper.format_results(all_cars_by_city)
    
    # Save the results to a JSON file
    output_file = "test_scrape_results.json"
    
    with open(output_file, 'w') as f:
        json.dump(formatted_results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    
    # Print a sample of the results
    if formatted_results:
        logger.info("Sample of results:")
        sample = formatted_results[0]
        city_domain = list(sample.keys())[0]
        car_details_list = sample[city_domain]
        
        logger.info(f"City: {city_domain}")
        logger.info(f"Number of car details: {len(car_details_list)}")
        
        if car_details_list:
            logger.info("First car details:")
            logger.info(json.dumps(car_details_list[0], indent=2))
    
    logger.info("Full scraping test completed")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test the enhanced Craigslist car data scraper')
    parser.add_argument('--test-type', type=str, choices=['links', 'details', 'full'], default='full',
                        help='Type of test to run (links, details, or full)')
    parser.add_argument('--cities', type=str, nargs='+',
                        help='List of city domains to test (e.g., newyork chicago)')
    parser.add_argument('--max-cities', type=int, default=2,
                        help='Maximum number of cities to test if cities is not specified')
    parser.add_argument('--max-links', type=int, default=3,
                        help='Maximum number of links to scrape per city')
    
    args = parser.parse_args()
    
    # Get the list of cities to test
    city_domains = args.cities if args.cities else None
    
    # Run the specified test
    if args.test_type == 'links':
        test_collect_links(city_domains, args.max_cities)
    elif args.test_type == 'details':
        test_scrape_details(city_domains, args.max_cities, args.max_links)
    else:  # full
        test_full_scrape(city_domains, args.max_cities, args.max_links)
