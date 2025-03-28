#!/bin/bash

# Script to run the USA Cars scraper daily
# This will be executed by a cron job

# Set the working directory to the project root
cd "$(dirname "$0")"

# Activate virtual environment if using one (uncomment and modify if needed)
# source /path/to/your/virtualenv/bin/activate

# Set the date for the output file
DATE=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="usa_cars_data_${DATE}.json"

# Run the Django management command
# Options:
# --save-to-db: Save results to the database
# --output: Specify output file
# --headless: Run in headless mode (no browser UI)
python carDataScraper/manage.py usa_cars_scrape --save-to-db --output "$OUTPUT_FILE"

# Log the completion
echo "USA Cars scraper completed at $(date)" >> usa_cars_scraper_cron.log
