import json
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from scraper.models import CraigslistCity, VehicleListing, VehiclePhoto
from usa_cars_scraper import USACarsScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'USA Cars Data Scraper for Craigslist - processes one subdomain at a time to avoid server overload'

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
            '--max-domains',
            type=int,
            default=None,
            help='Maximum number of domains to scrape (default: all)',
        )
        parser.add_argument(
            '--domains',
            nargs='+',
            help='List of specific domains to scrape (e.g., newyork chicago)',
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
            '--timeout',
            type=int,
            default=30,
            help='Timeout for page loads in seconds (default: 30)',
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum number of retries for failed requests (default: 3)',
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug mode (save screenshots)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting USA Cars Data Scraper for Craigslist...'))
        
        # Get options
        output_file = options.get('output')
        save_to_db = options.get('save_to_db', False)
        max_domains = options.get('max_domains')
        domains = options.get('domains')
        headless = not options.get('no_headless', False)
        timeout = options.get('timeout', 30)
        max_retries = options.get('max_retries', 3)
        debug = options.get('debug', False)
        
        self.stdout.write(f'Browser mode: {"Headless" if headless else "Visible"}')
        self.stdout.write(f'Timeout: {timeout} seconds')
        self.stdout.write(f'Max retries: {max_retries}')
        self.stdout.write(f'Debug mode: {"Enabled" if debug else "Disabled"}')
        
        if output_file and not options.get('no_save_to_file', False):
            self.stdout.write(f'Output will be saved to {output_file}')
        elif not options.get('no_save_to_file', False):
            self.stdout.write('Output will be saved to an auto-generated file')
        else:
            self.stdout.write('Results will not be saved to a file')
        
        if save_to_db:
            self.stdout.write('Results will be saved to the database')
        
        # Create and run the scraper
        scraper = USACarsScraper(
            timeout=timeout,
            headless=headless,
            max_retries=max_retries,
            debug=debug
        )
        
        # Run the scraper
        results = scraper.scrape_all_domains(
            output_file=output_file if not options.get('no_save_to_file', False) else None,
            max_domains=max_domains,
            specific_domains=domains
        )
        
        # Save to database if requested
        if save_to_db:
            self.save_to_database(results)
            self.stdout.write(self.style.SUCCESS('Results saved to database'))
        
        # Print summary
        domain_status = scraper.get_domain_status()
        completed_count = sum(1 for status in domain_status.values() if status == "completed")
        failed_count = sum(1 for status in domain_status.values() if status == "failed")
        
        self.stdout.write(self.style.SUCCESS('\nScraping completed!'))
        self.stdout.write(f'Total domains processed: {len(domain_status)}')
        self.stdout.write(f'Successful domains: {completed_count}')
        self.stdout.write(f'Failed domains: {failed_count}')
        
        if output_file and not options.get('no_save_to_file', False):
            self.stdout.write(f'Results saved to: {output_file}')
    
    def save_to_database(self, results):
        """
        Save the scraped data to the database
        
        Args:
            results (list): A list of dictionaries with scraped data and status information
        """
        for domain_result in results:
            domain = domain_result.get('domain', '')
            state = domain_result.get('state', '')
            status = domain_result.get('status', '')
            listings = domain_result.get('listings', [])
            
            if not domain:
                logger.warning("Domain not found in result, skipping")
                continue
            
            # Get or create the CraigslistCity object
            city, created = CraigslistCity.objects.get_or_create(
                domain=domain,
                defaults={'name': domain.capitalize()}
            )
            
            if created:
                logger.info(f"Created new city: {domain}")
            
            # Process each car listing
            for car_details in listings:
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
                    
                    # Parse the timestamp
                    posted_date = None
                    timestamp_str = car_details.get('timestamp')
                    if timestamp_str:
                        try:
                            from dateutil import parser
                            posted_date = parser.parse(timestamp_str)
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
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
