import json
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from scraper.models import CraigslistCity, VehicleListing, VehiclePhoto
from selenium_enhanced_scraper import SeleniumEnhancedCraigslistScraper, scrape_and_save, scrape_cities_concurrently

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Enhanced scraper for Craigslist car data using Selenium to avoid being blocked by the server'

    def add_arguments(self, parser):
        parser.add_argument(
            '--save-to-db',
            action='store_true',
            help='Save the scraped data to the database',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: auto-generated filename)',
        )
        parser.add_argument(
            '--max-workers',
            type=int,
            default=5,
            help='Maximum number of worker threads (default: 5)',
        )
        parser.add_argument(
            '--max-cities',
            type=int,
            default=None,
            help='Maximum number of cities to scrape (default: all)',
        )
        parser.add_argument(
            '--max-links',
            type=int,
            default=None,
            help='Maximum number of links to scrape per city (default: all)',
        )
        parser.add_argument(
            '--cities',
            nargs='+',
            help='List of city domains to scrape (e.g., newyork chicago)',
        )
        parser.add_argument(
            '--no-save-to-file',
            action='store_true',
            help='Do not save the scraped data to a JSON file (overrides default behavior)',
        )
        parser.add_argument(
            '--no-headless',
            action='store_true',
            help='Run the browser in non-headless mode (visible browser windows)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Size of batches for processing (default: 10)',
        )
        parser.add_argument(
            '--no-concurrent',
            action='store_true',
            help='Disable concurrent city scraping',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Selenium enhanced Craigslist car data scraper...'))
        
        # Get options
        max_workers = options.get('max_workers', 5)
        output_file = options.get('output')
        save_to_db = options.get('save_to_db', False)
        max_cities = options.get('max_cities')
        max_links = options.get('max_links')
        city_domains = options.get('cities')
        headless = not options.get('no_headless', False)
        batch_size = options.get('batch_size', 10)
        concurrent = not options.get('no_concurrent', False)
        
        self.stdout.write(f'Using {max_workers} worker threads')
        self.stdout.write(f'Browser mode: {"Headless" if headless else "Visible"}')
        self.stdout.write(f'Batch size: {batch_size}')
        self.stdout.write(f'Concurrent city scraping: {"Enabled" if concurrent else "Disabled"}')
        
        if output_file:
            self.stdout.write(f'Output will be saved to {output_file}')
        else:
            self.stdout.write('Output will be saved to an auto-generated file')
        
        if save_to_db:
            self.stdout.write('Results will be saved to the database')
        
        # Use the scrape_and_save function to handle the scraping
        formatted_results = scrape_and_save(
            max_workers=max_workers,
            output_file=output_file if not options.get('no_save_to_file', False) else None,
            max_cities=max_cities,
            max_links=max_links,
            city_domains=city_domains,
            headless=headless,
            batch_size=batch_size,
            concurrent=concurrent
        )
        
        # If no_save_to_file is True, we need to handle the output file differently
        if options.get('no_save_to_file', False):
            self.stdout.write(self.style.SUCCESS('Results not saved to a file as requested'))
        
        # Save to database if requested
        if save_to_db:
            # Convert the formatted results to the format expected by save_to_database
            all_cars_by_city = {}
            for city_data in formatted_results:
                for city_domain, car_details_list in city_data.items():
                    all_cars_by_city[city_domain] = car_details_list
            
            self.save_to_database(all_cars_by_city)
            self.stdout.write(self.style.SUCCESS('Results saved to database'))
        
        # Print a sample of the results
        if formatted_results:
            self.stdout.write('Sample of results:')
            sample = formatted_results[0]
            city_domain = list(sample.keys())[0]
            car_details_list = sample[city_domain]
            
            self.stdout.write(f'City: {city_domain}')
            self.stdout.write(f'Number of car details: {len(car_details_list)}')
            
            if car_details_list:
                self.stdout.write('First car details:')
                self.stdout.write(json.dumps(car_details_list[0], indent=2))
    
    def save_to_database(self, all_cars_by_city):
        """
        Save the scraped data to the database
        
        Args:
            all_cars_by_city (dict): A dictionary with city domains as keys and lists of car details as values
        """
        # Get or create CraigslistCity objects
        for city_domain, car_details_list in all_cars_by_city.items():
            # Find the city name from the domain
            scraper = SeleniumEnhancedCraigslistScraper()
            city_info = next((city for city in scraper.get_cities() if city['domain'] == city_domain), None)
            
            if not city_info:
                logger.warning(f"City info not found for domain: {city_domain}")
                continue
            
            city_name = city_info['name']
            
            # Get or create the CraigslistCity object
            city, created = CraigslistCity.objects.get_or_create(
                domain=city_domain,
                defaults={'name': city_name}
            )
            
            if created:
                logger.info(f"Created new city: {city_name} ({city_domain})")
            
            # Process each car listing
            for car_details in car_details_list:
                try:
                    # Extract the listing ID
                    listing_id = car_details.get('listing_id', '')
                    
                    if not listing_id:
                        # Try to extract from URL
                        url = car_details.get('url', '')
                        import re
                        id_match = re.search(r'/(\d+)\.html', url)
                        if id_match:
                            listing_id = id_match.group(1)
                    
                    if not listing_id:
                        logger.warning(f"Listing ID not found for URL: {car_details.get('url', '')}")
                        continue
                    
                    # Parse the posted date
                    posted_date = None
                    posted_date_str = car_details.get('posted_date')
                    if posted_date_str:
                        try:
                            from dateutil import parser
                            posted_date = parser.parse(posted_date_str)
                        except:
                            posted_date = timezone.now()
                    else:
                        posted_date = timezone.now()
                    
                    # Get or create the VehicleListing object
                    listing, created = VehicleListing.objects.update_or_create(
                        city=city,
                        listing_id=listing_id,
                        defaults={
                            'title': car_details.get('title', 'No Title'),
                            'price': car_details.get('price', ''),
                            'location': car_details.get('location', ''),
                            'url': car_details.get('url', ''),
                            'image_url': car_details.get('photo_urls', [''])[0] if car_details.get('photo_urls') else '',
                            'posted_date': posted_date,
                            'state': car_details.get('state', ''),
                            'city_name': car_details.get('city', ''),
                            'description': car_details.get('description', ''),
                            'phone_number': car_details.get('phone_number', '')
                        }
                    )
                    
                    if created:
                        logger.info(f"Created new listing: {listing.title}")
                    else:
                        logger.info(f"Updated existing listing: {listing.title}")
                    
                    # Add photos
                    photo_urls = car_details.get('photo_urls', [])
                    
                    # Delete existing photos
                    listing.photos.all().delete()
                    
                    # Add new photos
                    for photo_url in photo_urls:
                        VehiclePhoto.objects.create(
                            vehicle=listing,
                            url=photo_url
                        )
                    
                    logger.info(f"Added {len(photo_urls)} photos to listing: {listing.title}")
                
                except Exception as e:
                    logger.error(f"Error saving listing to database: {str(e)}")
                    continue
