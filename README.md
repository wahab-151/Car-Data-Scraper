# Car-Data-Scraper

A comprehensive tool for scraping car listing data from Craigslist across all major cities in the USA.

## Features

- Scrapes car listings from Craigslist for major US cities
- Multithreaded scraping for improved performance
- Formats data in a structured JSON format
- Saves results to a JSON file
- Optional database storage with Django ORM
- Both Django management command and standalone script available

## Installation

### Prerequisites

- Python 3.6+
- pipenv (for dependency management)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Car-Data-Scraper.git
   cd Car-Data-Scraper
   ```

2. Install dependencies:
   ```
   pipenv install
   pipenv shell
   ```

## Usage

### Option 1: Using the API Endpoints

The project provides several API endpoints:

1. **Scrape Formatted Data** - Returns data in the requested format: `[{"newyork":[car1, car2, ...]}, {"alabama":[car1, car2, ...]}]`
   ```
   GET /api/scrape-formatted-data/
   ```
   
   Query parameters:
   - `max_workers`: Maximum number of worker threads (default: 10)
   - `save_to_file`: Whether to save results to a file (default: false)
   - `save_to_db`: Whether to save results to the database (default: false)

2. **Scrape All Cities** - Returns data organized by city name
   ```
   GET /api/cars/
   ```
   
   Query parameters:
   - `save`: Whether to save results to the database (default: false)

3. **List Cities** - Returns a list of all Craigslist cities
   ```
   GET /api/cities/
   ```

4. **List Vehicles** - Returns a list of all vehicle listings
   ```
   GET /api/vehicles/
   ```
   
   Query parameters:
   - `city`: Filter by city domain (e.g., "newyork")
   - `search`: Filter by search term in title

To run the Django development server:
```bash
cd carDataScraper
python manage.py runserver
```

### Option 2: Using the Django Management Command

```bash
# Navigate to the Django project directory
cd carDataScraper

# Run the scraper
python manage.py scrape_craigslist

# Run with options
python manage.py scrape_craigslist --max-workers 20 --save-to-db --output cars.json
```

### Option 3: Using the Standalone Script

```bash
# Run the script directly
python scrape_craigslist_cars.py

# Run with options
python scrape_craigslist_cars.py --max-workers 20 --output cars.json
```

## Command Line Options

- `--max-workers`: Maximum number of worker threads (default: 10)
- `--output`: Custom output file path (default: auto-generated filename)
- `--save-to-db`: Save results to the database (Django command only)

## Output Format

The scraper outputs data in the following format:

```json
[
  {
    "newyork": [
      {
        "listing_id": "12345678",
        "title": "2018 Toyota Camry",
        "price": "$15,000",
        "location": "Manhattan",
        "url": "https://newyork.craigslist.org/...",
        "image_url": "https://images.craigslist.org/...",
        "posted_date": "2023-01-01T12:00:00"
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

## Supported Cities

The scraper includes support for major US cities including:
- New York
- Los Angeles
- Chicago
- Houston
- Phoenix
- Philadelphia
- San Antonio
- San Diego
- Dallas
- San Jose
- And many more...

## Extending

To add more cities, edit the `CRAIGSLIST_CITIES` list in `carDataScraper/scraper/utils/scraper.py`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
