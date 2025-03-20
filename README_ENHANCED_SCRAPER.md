# Enhanced Craigslist Car Data Scraper

This enhanced scraper is designed to collect car listing data from Craigslist in a two-phase approach:

1. First, it collects all car listing links from each city domain
2. Then, it visits each link to get detailed information about each car
3. Finally, it organizes the data by city in a specific format

## Features

- Collects links and car details in separate phases for better control
- Supports parallel scraping with configurable number of worker threads
- Handles various Craigslist HTML structures and formats
- Extracts comprehensive car details including:
  - Title, price, location
  - Description
  - Phone number (when available)
  - Photo URLs
  - Additional attributes
- Saves results to JSON files
- Optionally saves results to the Django database
- Provides detailed logging

## Usage

### Standalone Script

You can run the enhanced scraper as a standalone script:

```bash
python enhanced_scraper.py --max-workers 10 --output my_results.json
```

### Test Script

For testing purposes, you can use the test script with limited cities and listings:

```bash
# Test link collection only
python test_enhanced_scraper.py --test-type links --cities newyork chicago --max-links 5

# Test car details scraping only
python test_enhanced_scraper.py --test-type details --cities newyork chicago --max-links 3

# Test full scraping process
python test_enhanced_scraper.py --test-type full --cities newyork chicago --max-links 3
```

### Django Management Command

If you're using the Django project, you can use the management command:

```bash
# Scrape all cities and save to a JSON file (default behavior)
python manage.py enhanced_scrape --output my_results.json

# Scrape specific cities with limited links and save to the database
python manage.py enhanced_scrape --cities newyork chicago --max-links 10 --save-to-db

# Scrape a limited number of cities with all their links
python manage.py enhanced_scrape --max-cities 5

# Scrape without saving to a JSON file (override default behavior)
python manage.py enhanced_scrape --no-save-to-file
```

## Command Line Arguments

### Standalone Script (`enhanced_scraper.py`)

- `--max-workers`: Maximum number of worker threads (default: 10)
- `--output`: Output file path (default: auto-generated filename)

### Test Script (`test_enhanced_scraper.py`)

- `--test-type`: Type of test to run (links, details, or full)
- `--cities`: List of city domains to test (e.g., newyork chicago)
- `--max-cities`: Maximum number of cities to test if cities is not specified
- `--max-links`: Maximum number of links to scrape per city

### Django Management Command (`enhanced_scrape`)

- `--save-to-db`: Save the scraped data to the database
- `--output`: Output file path (default: auto-generated filename)
- `--max-workers`: Maximum number of worker threads (default: 10)
- `--max-cities`: Maximum number of cities to scrape (default: all)
- `--max-links`: Maximum number of links to scrape per city (default: all)
- `--cities`: List of city domains to scrape (e.g., newyork chicago)

## Output Format

The scraper outputs data in the following format:

```json
[
  {
    "newyork": [
      {
        "listing_id": "7835765436",
        "title": "2012 Volkswagen Eos 2dr Conv",
        "price": "$8,995",
        "location": "Lynbrook",
        "url": "https://newyork.craigslist.org/lgi/ctd/d/lynbrook-2012-volkswagen-eos-2dr-conv/7835765436.html",
        "posted_date": "2025-03-19T12:34:56",
        "state": "newyork",
        "city": "Lynbrook",
        "description": "Clean title, runs and drives great...",
        "phone_number": "(555) 123-4567",
        "photo_urls": [
          "https://images.craigslist.org/00J0J_tudP0uHP02_0cU09G_600x450.jpg",
          "https://images.craigslist.org/00808_cBF0qT5U4zz_0cU09G_600x450.jpg"
        ],
        "attributes": {
          "condition": "excellent",
          "cylinders": "4 cylinders",
          "drive": "fwd",
          "fuel": "gas",
          "odometer": "85000",
          "title status": "clean",
          "transmission": "automatic",
          "type": "convertible"
        }
      },
      // More car listings...
    ]
  },
  {
    "chicago": [
      // Chicago car listings...
    ]
  },
  // More cities...
]
```

## Requirements

- Python 3.6+
- requests
- beautifulsoup4
- concurrent.futures (standard library)
- Django (for the management command)
- python-dateutil (for date parsing)

## Notes

- The scraper respects Craigslist's robots.txt and uses a reasonable delay between requests
- For large-scale scraping, consider using proxies and rotating user agents
- Be aware of Craigslist's terms of service when using this scraper
