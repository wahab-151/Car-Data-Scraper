#!/usr/bin/env python
"""
Test script for the USA Cars Data Scraper.
This script tests the scraper with a limited number of domains and listings.
"""

import argparse
import logging
import os
import sys
import datetime
import traceback
from usa_cars_scraper import USACarsScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the test."""
    parser = argparse.ArgumentParser(description='Test the USA Cars Data Scraper')
    parser.add_argument('--domains', nargs='+', default=['newyork', 'chicago', 'losangeles'], 
                        help='List of domains to test (default: newyork chicago losangeles)')
    parser.add_argument('--max-domains', type=int, default=3, 
                        help='Maximum number of domains to test (default: 3)')
    parser.add_argument('--max-pages', type=int, default=1, 
                        help='Maximum number of pages to scrape per domain (default: 1)')
    parser.add_argument('--max-listings', type=int, default=2, 
                        help='Maximum number of listings to scrape per domain (default: 2)')
    parser.add_argument('--no-headless', action='store_true', 
                        help='Run the browser in non-headless mode (visible browser windows)')
    parser.add_argument('--debug', action='store_true', 
                        help='Enable debug mode (save screenshots)')
    
    args = parser.parse_args()
    
    # Generate output filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"test_usa_cars_multiple_{timestamp}.json"
    
    # Limit the number of domains
    domains_to_test = args.domains[:args.max_domains]
    
    logger.info(f"Testing USA Cars Data Scraper with domains: {', '.join(domains_to_test)}")
    logger.info(f"Max domains: {args.max_domains}")
    logger.info(f"Max pages: {args.max_pages}")
    logger.info(f"Max listings: {args.max_listings}")
    logger.info(f"Headless mode: {not args.no_headless}")
    logger.info(f"Debug mode: {args.debug}")
    logger.info(f"Output file: {output_file}")
    
    # Create the scraper
    scraper = USACarsScraper(
        headless=not args.no_headless,
        debug=args.debug
    )
    
    # Override the _process_domain method to limit the number of pages and listings
    original_process_domain = scraper._process_domain
    
    def limited_process_domain(driver, domain, state, url):
        """Limited version of _process_domain that only processes a limited number of pages and listings."""
        domain_results = []
        processed_links = set()
        
        # Process the first page
        current_page_url = url
        page_num = 1
        
        while current_page_url and page_num <= args.max_pages:
            logger.info(f"Processing page {page_num} for domain {domain}: {current_page_url}")
            
            # Process the current page
            next_page_url, links = scraper._process_listing_page(driver, current_page_url, domain, processed_links)
            
            # Limit the number of links
            links = links[:args.max_listings]
            
            # Process each link
            for link in links:
                if link not in processed_links:
                    processed_links.add(link)
                    
                    # Scrape car details
                    car_details = scraper._scrape_car_details(driver, link, domain, state)
                    
                    if car_details:
                        domain_results.append(car_details)
                        logger.info(f"Scraped details for listing: {car_details.get('title', 'No Title')}")
                    
                    # Check if we've reached the maximum number of listings
                    if len(domain_results) >= args.max_listings:
                        logger.info(f"Reached maximum number of listings ({args.max_listings})")
                        return domain_results
            
            # Move to the next page
            current_page_url = next_page_url
            
            # Increment page number
            page_num += 1
        
        logger.info(f"Finished processing {len(domain_results)} listings for domain {domain}")
        return domain_results
    
    # Replace the _process_domain method with our limited version
    scraper._process_domain = limited_process_domain
    
    try:
        # Get all domains
        all_domains = scraper.get_all_domains()
        
        # Initialize results
        all_results = []
        
        # Process each domain
        for domain in domains_to_test:
            logger.info(f"Testing domain: {domain}")
            
            # Find the state for the domain
            domain_info = next((d for d in all_domains if d["domain"] == domain), None)
            
            if not domain_info:
                logger.error(f"Domain {domain} not found in the list of domains")
                continue
            
            state = domain_info["state"]
            
            try:
                # Scrape the domain
                results = scraper.scrape_domain(domain, state)
                
                # Format the results
                formatted_results = {
                    "domain": domain,
                    "state": state,
                    "status": "completed",
                    "listings": results,
                    "count": len(results)
                }
                
                # Add to all results
                all_results.append(formatted_results)
                
                logger.info(f"Successfully scraped {len(results)} listings from {domain}")
            except Exception as e:
                logger.error(f"Error scraping domain {domain}: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Add failed result
                all_results.append({
                    "domain": domain,
                    "state": state,
                    "status": "failed",
                    "listings": [],
                    "count": 0,
                    "error": str(e)
                })
        
        # Save the results
        import json
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        logger.info(f"Test completed successfully!")
        logger.info(f"Tested {len(all_results)} domains")
        logger.info(f"Results saved to {output_file}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
