import json
import os
import sys
import logging
from datetime import datetime

# Add the parent directory to the path so we can import the scraper module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scraper.utils.scraper import CraigslistScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scrape_and_format_data(max_workers=10, output_file=None, save_to_db=False, save_to_file=True):
    """
    Scrape car data from Craigslist for all USA cities and format the response
    as requested: [{"newyork":[car1, car2, ...]}, {"alabama":[car1, car2, ...]}]
    
    Args:
        max_workers (int): Maximum number of worker threads
        output_file (str): Output file path (if None and save_to_file is True, auto-generate filename)
        save_to_db (bool): Whether to save the results to the database
        save_to_file (bool): Whether to save the results to a file
        
    Returns:
        tuple: (formatted_results, output_file_path or None)
    """
    logger.info("Starting to scrape Craigslist car data for all USA cities...")
    
    # Create a scraper instance
    scraper = CraigslistScraper(max_workers=max_workers)
    
    # Get the list of cities
    cities = scraper.get_cities()
    logger.info(f"Found {len(cities)} cities to scrape")
    
    # Scrape all cities
    results_by_city = scraper.scrape_all_cities()
    logger.info(f"Successfully scraped {len(results_by_city)} cities")
    
    # Format the results as requested
    formatted_results = []
    for city_name, listings in results_by_city.items():
        # Find the domain for this city
        city_info = next((city for city in cities if city['name'] == city_name), None)
        if city_info:
            city_domain = city_info['domain']
            formatted_results.append({city_domain: listings})
    
    logger.info(f"Formatted results for {len(formatted_results)} cities")
    
    # Save the results to a JSON file if requested
    if save_to_file:
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"craigslist_cars_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(formatted_results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
    else:
        output_file = None
        logger.info("Results not saved to file as requested")
    
    # Save to database if requested
    if save_to_db:
        try:
            # Import here to avoid circular imports
            from django.conf import settings
            from scraper.views import ScrapeAllCitiesView
            
            logger.info("Saving results to database...")
            view = ScrapeAllCitiesView()
            results_dict = {city_name: listings for item in formatted_results for city_name, listings in item.items()}
            view._save_to_database(results_dict)
            logger.info("Results saved to database")
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
    
    return formatted_results, output_file

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape car data from Craigslist')
    parser.add_argument('--max-workers', type=int, default=10, help='Maximum number of worker threads')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--save-to-db', action='store_true', help='Save results to database')
    parser.add_argument('--save-to-file', action='store_true', help='Save results to a file')
    
    args = parser.parse_args()
    
    results, output_file = scrape_and_format_data(
        max_workers=args.max_workers,
        output_file=args.output,
        save_to_db=args.save_to_db,
        save_to_file=args.save_to_file
    )
    
    print(f"Scraped data from {len(results)} cities")
    if output_file:
        print(f"Results saved to {output_file}")
    else:
        print("Results were not saved to a file")
    if results:
        print(f"First result: {json.dumps(results[0], indent=2)}")
