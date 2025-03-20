import json
import logging
from concurrent.futures import ThreadPoolExecutor
from django.core.management.base import BaseCommand
from django.utils import timezone
from scraper.models import CraigslistCity, VehicleListing, VehiclePhoto
from enhanced_scraper import EnhancedCraigslistScraper, scrape_and_save

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Enhanced scraper for Craigslist car data that first collects all links and then visits each link'

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
            default=10,
            help='Maximum number of worker threads (default: 10)',
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

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting enhanced Craigslist car data scraper...'))
        
        # Get options
        max_workers = options.get('max_workers', 10)
        output_file = options.get('output')
        save_to_db = options.get('save_to_db', False)
        max_cities = options.get('max_cities')
        max_links = options.get('max_links')
        city_domains = options.get('cities')
        
        self.stdout.write(f'Using {max_workers} worker threads')
        
        if output_file:
            self.stdout.write(f'Output will be saved to {output_file}')
        else:
            self.stdout.write('Output will be saved to an auto-generated file')
        
        if save_to_db:
            self.stdout.write('Results will be saved to the database')
        
        # Create a scraper instance
        scraper = EnhancedCraigslistScraper(max_workers=max_workers)
        
        # Get the list of cities to scrape
        all_cities = scraper.get_cities()
        
        if city_domains:
            cities_to_scrape = [city for city in all_cities if city['domain'] in city_domains]
            self.stdout.write(f'Scraping {len(cities_to_scrape)} specified cities')
        elif max_cities:
            cities_to_scrape = all_cities[:max_cities]
            self.stdout.write(f'Scraping first {len(cities_to_scrape)} cities')
        else:
            cities_to_scrape = all_cities
            self.stdout.write(f'Scraping all {len(cities_to_scrape)} cities')
        
        city_domains_to_scrape = [city['domain'] for city in cities_to_scrape]
        
        # Phase 1: Collect all car links from each city
        all_links_by_city = {}
        
        for city_domain in city_domains_to_scrape:
            self.stdout.write(f'Collecting links for {city_domain}...')
            result = scraper.collect_car_links(city_domain)
            
            links = result['links']
            self.stdout.write(f'Found {len(links)} links for {city_domain}')
            
            # Limit the number of links to scrape if specified
            if max_links:
                links = links[:max_links]
                self.stdout.write(f'Limited to {len(links)} links for {city_domain}')
            
            if links:
                all_links_by_city[city_domain] = links
        
        self.stdout.write(self.style.SUCCESS(f'Collected links from {len(all_links_by_city)} cities'))
        
        # Phase 2: Visit each link to get detailed information
        all_cars_by_city = {}
        
        for city_domain, links in all_links_by_city.items():
            self.stdout.write(f'Scraping {len(links)} car details for {city_domain}')
            
            car_details_list = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                car_results = list(executor.map(scraper.scrape_car_details, links))
            
            for car_details in car_results:
                if 'error' not in car_details:
                    car_details_list.append(car_details)
            
            all_cars_by_city[city_domain] = car_details_list
            
            self.stdout.write(f'Scraped {len(car_details_list)} car details for {city_domain}')
        
        # Format the results
        formatted_results = []
        
        for city_domain, car_details_list in all_cars_by_city.items():
            formatted_results.append({city_domain: car_details_list})
        
        # Save the results to a JSON file if not disabled
        no_save_to_file = options.get('no_save_to_file', False)
        
        if not no_save_to_file:
            if output_file is None:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"craigslist_cars_enhanced_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(formatted_results, f, indent=2)
            
            self.stdout.write(self.style.SUCCESS(f'Results saved to {output_file}'))
        else:
            self.stdout.write(self.style.SUCCESS('Results not saved to a file as requested'))
        
        # Save to database if requested
        if save_to_db:
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
            scraper = EnhancedCraigslistScraper()
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
