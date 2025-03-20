#!/usr/bin/env python
"""
Standalone script to scrape car data from Craigslist for all USA cities.
This script can be run directly without Django.
"""

import os
import sys
import argparse

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description='Scrape car data from Craigslist for all USA cities')
    parser.add_argument(
        '--max-workers',
        type=int,
        default=10,
        help='Maximum number of worker threads (default: 10)',
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: auto-generated filename)',
    )
    parser.add_argument(
        '--save-to-file',
        action='store_true',
        default=True,
        help='Save results to a file (default: True)',
    )
    
    args = parser.parse_args()
    
    # Import here to avoid circular imports
    from carDataScraper.scraper.utils.scrape_and_format import scrape_and_format_data
    
    print('Starting to scrape Craigslist car data...')
    print(f'Using {args.max_workers} worker threads')
    if args.save_to_file:
        if args.output:
            print(f'Output will be saved to {args.output}')
        else:
            print('Output will be saved to an auto-generated file')
    else:
        print('Results will not be saved to a file')
    
    # Call the scrape_and_format_data function
    results, output_file = scrape_and_format_data(
        max_workers=args.max_workers,
        output_file=args.output,
        save_to_db=False,  # Don't save to database in standalone mode
        save_to_file=args.save_to_file
    )
    
    # Print summary
    print(f'Successfully scraped data from {len(results)} cities')
    if output_file:
        print(f'Results saved to {output_file}')
    else:
        print('Results were not saved to a file')
    
    # Print a sample of the results
    if results:
        print('Sample of results:')
        sample = results[0]
        city_domain = list(sample.keys())[0]
        listings = sample[city_domain]
        
        print(f'City: {city_domain}')
        print(f'Number of listings: {len(listings)}')
        
        if listings:
            import json
            print('First listing:')
            print(json.dumps(listings[0], indent=2))

if __name__ == '__main__':
    main()
