import json
from django.core.management.base import BaseCommand
from scraper.utils.scrape_and_format import scrape_and_format_data

class Command(BaseCommand):
    help = 'Scrape car data from Craigslist for all USA cities'

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
            '--save-to-file',
            action='store_true',
            default=True,
            help='Save results to a file (default: True)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to scrape Craigslist car data...'))
        
        # Get options
        max_workers = options.get('max_workers', 10)
        output_file = options.get('output')
        save_to_db = options.get('save_to_db', False)
        
        save_to_file = options.get('save_to_file', True)
        
        self.stdout.write(f'Using {max_workers} worker threads')
        if save_to_file:
            if output_file:
                self.stdout.write(f'Output will be saved to {output_file}')
            else:
                self.stdout.write('Output will be saved to an auto-generated file')
        else:
            self.stdout.write('Results will not be saved to a file')
        if save_to_db:
            self.stdout.write('Results will be saved to the database')
        
        # Call the scrape_and_format_data function
        results, output_file = scrape_and_format_data(
            max_workers=max_workers,
            output_file=output_file,
            save_to_db=save_to_db,
            save_to_file=save_to_file
        )
        
        # Print summary
        self.stdout.write(self.style.SUCCESS(f'Successfully scraped data from {len(results)} cities'))
        if output_file:
            self.stdout.write(self.style.SUCCESS(f'Results saved to {output_file}'))
        else:
            self.stdout.write(self.style.SUCCESS('Results were not saved to a file'))
        
        # Print a sample of the results
        if results:
            self.stdout.write('Sample of results:')
            sample = results[0]
            city_domain = list(sample.keys())[0]
            listings = sample[city_domain]
            
            self.stdout.write(f'City: {city_domain}')
            self.stdout.write(f'Number of listings: {len(listings)}')
            
            if listings:
                self.stdout.write('First listing:')
                self.stdout.write(json.dumps(listings[0], indent=2))
