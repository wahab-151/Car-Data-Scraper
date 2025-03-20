#!/usr/bin/env python
"""
Enhanced Craigslist car data scraper that:
1. First collects all car listing links from each city domain
2. Then visits each link to get detailed information about each car
3. Organizes the data by city in a specific format
"""

import re
import json
import logging
import time
import datetime
import requests
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# List of major Craigslist subdomains in the USA
CRAIGSLIST_CITIES = [
    {"name": "New York", "domain": "newyork"},
    {"name": "Los Angeles", "domain": "losangeles"},
    {"name": "Chicago", "domain": "chicago"},
    {"name": "Houston", "domain": "houston"},
    {"name": "Phoenix", "domain": "phoenix"},
    {"name": "Philadelphia", "domain": "philadelphia"},
    {"name": "San Antonio", "domain": "sanantonio"},
    {"name": "San Diego", "domain": "sandiego"},
    {"name": "Dallas", "domain": "dallas"},
    {"name": "San Jose", "domain": "sanjose"},
    {"name": "Austin", "domain": "austin"},
    {"name": "Jacksonville", "domain": "jacksonville"},
    {"name": "Fort Worth", "domain": "fortworth"},
    {"name": "Columbus", "domain": "columbus"},
    {"name": "Charlotte", "domain": "charlotte"},
    {"name": "San Francisco", "domain": "sfbay"},
    {"name": "Indianapolis", "domain": "indianapolis"},
    {"name": "Seattle", "domain": "seattle"},
    {"name": "Denver", "domain": "denver"},
    {"name": "Boston", "domain": "boston"},
    {"name": "Las Vegas", "domain": "lasvegas"},
    {"name": "Portland", "domain": "portland"},
    {"name": "Oklahoma City", "domain": "oklahomacity"},
    {"name": "Detroit", "domain": "detroit"},
    {"name": "Memphis", "domain": "memphis"},
    {"name": "Atlanta", "domain": "atlanta"},
    {"name": "Baltimore", "domain": "baltimore"},
    {"name": "Montgomery", "domain": "montgomery"},
    {"name": "Birmingham", "domain": "bham"},
    {"name": "Huntsville", "domain": "huntsville"},
    {"name": "Mobile", "domain": "mobile"},
    {"name": "Sacramento", "domain": "sacramento"},
]

class EnhancedCraigslistScraper:
    def __init__(self, max_workers=10, timeout=30):
        self.max_workers = max_workers
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
    
    def get_cities(self):
        """Returns the list of Craigslist cities"""
        return CRAIGSLIST_CITIES
    
    def collect_car_links(self, city_domain):
        """
        Collect all car listing links from a city domain
        
        Args:
            city_domain (str): The Craigslist city domain (e.g., 'newyork')
            
        Returns:
            dict: A dictionary with city_domain and list of car links
        """
        try:
            url = f"https://{city_domain}.craigslist.org/search/cta"
            logger.info(f"Scraping {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            links = []
            
            if 'json' in response.headers.get('Content-Type', ''):
                # Some Craigslist sites return JSON
                data = response.json()
                for item in data.get('items', []):
                    if 'url' in item:
                        links.append(item['url'])
            else:
                # Otherwise parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Debug: Print a sample of the HTML to understand the structure
                logger.info(f"HTML sample: {str(soup)[:1000]}")
                
                # Debug: Print the number of elements found with each selector
                logger.info(f"Found {len(soup.select('.result-info'))} .result-info elements")
                logger.info(f"Found {len(soup.select('.cl-static-search-result'))} .cl-static-search-result elements")
                logger.info(f"Found {len(soup.select('.gallery-card'))} .gallery-card elements")
                logger.info(f"Found {len(soup.select('.cl-search-result'))} .cl-search-result elements")
                logger.info(f"Found {len(soup.select('.cl-search-result.cl-search-view-mode-gallery'))} .cl-search-result.cl-search-view-mode-gallery elements")
                logger.info(f"Found {len(soup.select('a.cl-app-anchor.text-only.posting-title'))} a.cl-app-anchor.text-only.posting-title elements")
                
                # Debug: Print more details about the .cl-static-search-result elements
                static_search_results = soup.select('.cl-static-search-result')
                if static_search_results:
                    logger.info(f"First .cl-static-search-result element: {static_search_results[0]}")
                    # Check for links within the first element
                    links_in_first = static_search_results[0].select('a')
                    logger.info(f"Found {len(links_in_first)} links in first .cl-static-search-result element")
                    for i, link in enumerate(links_in_first[:3]):  # Print first 3 links
                        logger.info(f"Link {i+1}: {link}")
                
                # Extract links from .cl-static-search-result elements
                if static_search_results:
                    for result in static_search_results:
                        # Each .cl-static-search-result contains an <a> element with the href
                        link_el = result.select_one('a')
                        if link_el and 'href' in link_el.attrs:
                            links.append(link_el['href'])
                
                # Extract links from .cl-search-result.cl-search-view-mode-gallery elements (from user's HTML snippet)
                gallery_search_results = soup.select('.cl-search-result.cl-search-view-mode-gallery')
                if gallery_search_results:
                    logger.info(f"First .cl-search-result.cl-search-view-mode-gallery element: {gallery_search_results[0]}")
                    for result in gallery_search_results:
                        # Look for the link with class 'cl-app-anchor text-only posting-title'
                        link_el = result.select_one('a.cl-app-anchor.text-only.posting-title')
                        if link_el and 'href' in link_el.attrs:
                            links.append(link_el['href'])
                
                # If no links found, try other selectors
                if not links:
                    # Find all listing elements - try different selectors as Craigslist's HTML structure can vary
                    listing_elements = (
                        soup.select('.result-info') or 
                        soup.select('.gallery-card') or
                        soup.select('.cl-search-result')
                    )
                    
                    for listing_el in listing_elements:
                        # Try different selectors for the link
                        link_el = (
                            listing_el.select_one('.result-title') or 
                            listing_el.select_one('h3 a') or
                            listing_el.select_one('a.cl-app-anchor') or
                            listing_el.select_one('a.posting-title') or
                            listing_el.select_one('a.cl-app-anchor.text-only.posting-title')
                        )
                        
                        if link_el and 'href' in link_el.attrs:
                            links.append(link_el['href'])
                
                # If still no links found, try direct selection of the link elements
                if not links:
                    direct_links = soup.select('a.cl-app-anchor.text-only.posting-title')
                    for link_el in direct_links:
                        if 'href' in link_el.attrs:
                            links.append(link_el['href'])
            
            logger.info(f"Found {len(links)} car links for {city_domain}")
            linksss={
                "city_domain": city_domain,
                "links": links
            }
            return {
                "city_domain": city_domain,
                "links": links
            }
        
        except Exception as e:
            logger.error(f"Error collecting links for {city_domain}: {str(e)}")
            return {
                "city_domain": city_domain,
                "links": []
            }
    
    def scrape_car_details(self, url):
        """
        Scrape detailed information from an individual car listing page
        
        Args:
            url (str): The URL of the car listing
            
        Returns:
            dict: A dictionary with car details
        """
        try:
            logger.info(f"Scraping detailed listing: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic information
            title_el = soup.select_one('h1.postingtitle') or soup.select_one('span.postingtitletext') or soup.select_one('span.label') or soup.select_one('a.cl-app-anchor.text-only.posting-title span.label')
            title = title_el.text.strip() if title_el else 'No Title'
            
            # Extract price
            price_el = soup.select_one('span.price') or soup.select_one('.price') or soup.select_one('span.priceinfo') or soup.select_one('.meta-line .priceinfo')
            price = price_el.text.strip() if price_el else ''
            
            # Extract description
            description_el = soup.select_one('#postingbody')
            description = description_el.text.strip() if description_el else ''
            
            # Remove "QR Code Link to This Post" text if present
            description = re.sub(r'QR Code Link to This Post\s*', '', description).strip()
            
            # Extract all image URLs
            photo_urls = []
            
            # Method 1: Try different selectors for images as Craigslist's HTML structure can vary
            gallery = (
                soup.select('.gallery .swipe img') or 
                soup.select('#thumbs .thumb img') or 
                soup.select('.gallery-image') or
                soup.select('.swipe-wrap img') or
                soup.select('.swipe-wrap div[data-index] img')
            )
            
            if gallery:
                for img in gallery:
                    if 'src' in img.attrs:
                        # Convert thumbnail URL to full-size image URL
                        img_url = img['src']
                        # Replace thumbnail size with full size if needed
                        img_url = re.sub(r'_\d+x\d+\.jpg', '_600x450.jpg', img_url)
                        if img_url not in photo_urls:  # Avoid duplicates
                            photo_urls.append(img_url)
            
            # Method 2: Look for image data in JavaScript variables
            if not photo_urls:
                script_tags = soup.find_all('script')
                for script in script_tags:
                    script_text = script.string
                    if script_text and 'var imgList' in script_text:
                        # Extract image IDs from JavaScript
                        img_list_match = re.search(r'var imgList = \[(.*?)\]', script_text, re.DOTALL)
                        if img_list_match:
                            img_list_str = img_list_match.group(1)
                            img_ids = re.findall(r'"([^"]+)"', img_list_str)
                            for img_id in img_ids:
                                img_url = f"https://images.craigslist.org/{img_id}_600x450.jpg"
                                photo_urls.append(img_url)
            
            # Method 3: If still no images found, try to find them in the page source
            if not photo_urls:
                # Look for image URLs in the page source
                img_urls = re.findall(r'https://images\.craigslist\.org/[^"\']+\.jpg', str(soup))
                for img_url in img_urls:
                    # Convert to full-size image URL
                    img_url = re.sub(r'_\d+x\d+\.jpg', '_600x450.jpg', img_url)
                    if img_url not in photo_urls:
                        photo_urls.append(img_url)
            
            # Try to extract phone number (this is challenging as Craigslist often hides it)
            phone_number = ''
            # Look for phone number patterns in the description
            phone_matches = re.findall(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', description)
            if phone_matches:
                phone_number = phone_matches[0]
            
            # Extract state and city from URL
            parsed_url = urlparse(url)
            domain_parts = parsed_url.netloc.split('.')
            state = domain_parts[0] if domain_parts else ''
            
            # Extract city from URL path or location
            path_parts = parsed_url.path.split('/')
            city = ''
            if len(path_parts) > 3:
                # Try to extract from URL path (e.g., /lgi/ctd/d/lynbrook-...)
                city_part = path_parts[4] if len(path_parts) > 4 else ''
                if city_part:
                    city_match = re.match(r'([a-zA-Z\-]+)', city_part)
                    if city_match:
                        city = city_match.group(1).replace('-', ' ').title()
            
            # Extract additional details from the listing
            attributes = {}
            
            # Look for the attributes section
            attr_groups = soup.select('.attrgroup')
            for group in attr_groups:
                spans = group.select('span')
                for span in spans:
                    text = span.text.strip()
                    if ':' in text:
                        key, value = text.split(':', 1)
                        attributes[key.strip()] = value.strip()
                    else:
                        # Some attributes don't have a key:value format
                        attributes[text] = True
            
            # Try to extract mileage from meta information
            meta_el = soup.select_one('.meta-line .meta')
            if meta_el:
                meta_text = meta_el.text.strip()
                # Look for mileage pattern (e.g., "149k mi")
                mileage_match = re.search(r'(\d+[k]?\s*mi)', meta_text)
                if mileage_match:
                    mileage = mileage_match.group(1)
                    attributes['odometer'] = mileage
            
            # Extract listing ID
            listing_id = ''
            id_match = re.search(r'/(\d+)\.html', url)
            if id_match:
                listing_id = id_match.group(1)
            
            # Extract posting date
            posted_date = datetime.datetime.now().isoformat()
            date_el = soup.select_one('.date') or soup.select_one('.postinginfos .date')
            if date_el:
                date_text = date_el.text.strip()
                try:
                    # Try to parse the date
                    from dateutil import parser
                    posted_date = parser.parse(date_text).isoformat()
                except:
                    pass
            
            # Extract location
            location = ''
            location_el = soup.select_one('.postingtitletext .price + small') or soup.select_one('.postinginfos .location') or soup.select_one('.meta-line .meta')
            if location_el:
                location = location_el.text.strip().strip('()')
                
                # If the meta element contains multiple pieces of information separated by separators
                if 'meta' in location_el.get('class', []):
                    # Try to extract just the location part
                    location_parts = re.split(r'<span class="separator"></span>', str(location_el))
                    if len(location_parts) > 1:
                        # The last part might be the location
                        location = BeautifulSoup(location_parts[-1], 'html.parser').text.strip()
            
            # Create the car details dictionary
            car_details = {
                'listing_id': listing_id,
                'title': title,
                'price': price,
                'location': location,
                'url': url,
                'posted_date': posted_date,
                'state': state,
                'city': city,
                'description': description,
                'phone_number': phone_number,
                'photo_urls': photo_urls,
                'attributes': attributes
            }
            
            return car_details
            
        except Exception as e:
            logger.error(f"Error scraping listing details for {url}: {str(e)}")
            return {
                'url': url,
                'error': str(e)
            }
    
    def scrape_all_cities(self):
        """
        Scrape all cities in two phases:
        1. Collect all car links from each city
        2. Visit each link to get detailed information
        
        Returns:
            dict: A dictionary with city domains as keys and lists of car details as values
        """
        start_time = time.time()
        logger.info("Starting to scrape all Craigslist cities...")
        
        # Phase 1: Collect all car links from each city
        city_domains = [city['domain'] for city in self.get_cities()]
        all_links_by_city = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            link_results = list(executor.map(self.collect_car_links, city_domains))
        
        for result in link_results:
            city_domain = result['city_domain']
            links = result['links']
            if links:
                all_links_by_city[city_domain] = links
        
        logger.info(f"Collected links from {len(all_links_by_city)} cities")
        
        # Phase 2: Visit each link to get detailed information
        all_cars_by_city = {}
        
        for city_domain, links in all_links_by_city.items():
            logger.info(f"Scraping {len(links)} car details for {city_domain}")
            
            # Limit the number of links to scrape (for testing or to avoid overloading)
            # links = links[:10]  # Uncomment to limit the number of links
            
            car_details_list = []
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                car_results = list(executor.map(self.scrape_car_details, links))
            
            for car_details in car_results:
                if 'error' not in car_details:
                    car_details_list.append(car_details)
            
            all_cars_by_city[city_domain] = car_details_list
            
            logger.info(f"Scraped {len(car_details_list)} car details for {city_domain}")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Completed scraping all cities in {elapsed_time:.2f} seconds. Found data for {len(all_cars_by_city)} cities.")
        
        return all_cars_by_city
    
    def format_results(self, all_cars_by_city):
        """
        Format the results as requested:
        [
            {"newyork": [car1, car2, ...]},
            {"alabama": [car1, car2, ...]}
        ]
        
        Args:
            all_cars_by_city (dict): A dictionary with city domains as keys and lists of car details as values
            
        Returns:
            list: A list of dictionaries with city domains as keys and lists of car details as values
        """
        formatted_results = []
        
        for city_domain, car_details_list in all_cars_by_city.items():
            formatted_results.append({city_domain: car_details_list})
        
        return formatted_results

def scrape_and_save(max_workers=10, output_file=None):
    """
    Scrape car data from Craigslist for all USA cities and save to a file
    
    Args:
        max_workers (int): Maximum number of worker threads
        output_file (str): Output file path (if None, auto-generate filename)
        
    Returns:
        tuple: (formatted_results, output_file_path)
    """
    # Create a scraper instance
    scraper = EnhancedCraigslistScraper(max_workers=max_workers)
    
    # Scrape all cities
    all_cars_by_city = scraper.scrape_all_cities()
    
    # Format the results
    formatted_results = scraper.format_results(all_cars_by_city)
    
    # Save the results to a JSON file
    if output_file is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"craigslist_cars_enhanced_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(formatted_results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    
    return formatted_results, output_file

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Craigslist car data scraper')
    parser.add_argument('--max-workers', type=int, default=10, help='Maximum number of worker threads')
    parser.add_argument('--output', type=str, help='Output file path')
    
    args = parser.parse_args()
    
    results, output_file = scrape_and_save(
        max_workers=args.max_workers,
        output_file=args.output
    )
    
    print(f"Scraped data from {len(results)} cities")
    print(f"Results saved to {output_file}")
    
    # Print a sample of the results
    if results:
        print("Sample of results:")
        sample = results[0]
        city_domain = list(sample.keys())[0]
        car_details_list = sample[city_domain]
        
        print(f"City: {city_domain}")
        print(f"Number of car details: {len(car_details_list)}")
        
        if car_details_list:
            print("First car details:")
            print(json.dumps(car_details_list[0], indent=2))
