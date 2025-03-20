import re
import json
import logging
import time
import datetime
import requests
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from django.conf import settings
from urllib.parse import urlparse

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

class CraigslistScraper:
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
    
    def scrape_city(self, city_domain):
        """Scrape vehicle listings for a single city"""
        try:
            url = f"https://{city_domain}.craigslist.org/search/cta"
            logger.info(f"Scraping {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            if 'json' in response.headers.get('Content-Type', ''):
                # Some Craigslist sites return JSON
                data = response.json()
                return self._parse_json_listings(data, city_domain)
            else:
                # Otherwise parse HTML
                return self._parse_html_listings(response.text, city_domain)
        
        except Exception as e:
            logger.error(f"Error scraping {city_domain}: {str(e)}")
            return {
                "city_domain": city_domain,
                "success": False,
                "error": str(e),
                "listings": []
            }
    
    def _parse_json_listings(self, data, city_domain):
        """Parse JSON response from Craigslist"""
        listings = []
        
        for item in data.get('items', []):
            listing = {
                'listing_id': item.get('id', ''),
                'title': item.get('title', 'No Title'),
                'price': item.get('price', ''),
                'location': item.get('location', ''),
                'url': item.get('url', ''),
                'image_url': item.get('imageUrl', item.get('image', '')),
                'posted_date': item.get('date', datetime.datetime.now().isoformat())
            }
            listings.append(listing)
            
        return {
            "city_domain": city_domain,
            "success": True,
            "listings": listings
        }
    
    def _scrape_listing_details(self, url):
        """Scrape detailed information from an individual listing page"""
        try:
            logger.info(f"Scraping detailed listing: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract description
            description_el = soup.select_one('#postingbody')
            description = description_el.text.strip() if description_el else ''
            
            # Remove "QR Code Link to This Post" text if present
            description = re.sub(r'QR Code Link to This Post\s*', '', description).strip()
            
            # Extract all image URLs
            photo_urls = []
            
            # Method 1: Try different selectors for images as Craigslist's HTML structure can vary
            gallery = soup.select('.gallery .swipe img') or soup.select('#thumbs .thumb img') or soup.select('.gallery-image')
            
            if gallery:
                for img in gallery:
                    if 'src' in img.attrs:
                        # Convert thumbnail URL to full-size image URL
                        img_url = img['src']
                        # Replace thumbnail size with full size if needed
                        img_url = re.sub(r'_\d+x\d+\.jpg', '_600x450.jpg', img_url)
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
                        
            # Method 4: Look for data-ids attribute in the gallery element
            if not photo_urls:
                gallery_el = soup.select_one('.gallery')
                if gallery_el and 'data-imgs' in gallery_el.attrs:
                    try:
                        # Parse the data-imgs attribute which might contain JSON
                        import json
                        imgs_data = json.loads(gallery_el['data-imgs'])
                        for img_data in imgs_data:
                            if 'url' in img_data:
                                photo_urls.append(img_data['url'])
                            elif 'id' in img_data:
                                img_url = f"https://images.craigslist.org/{img_data['id']}_600x450.jpg"
                                photo_urls.append(img_url)
                    except:
                        pass
            
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
            
            return {
                'description': description,
                'phone_number': phone_number,
                'photo_urls': photo_urls,
                'state': state,
                'city': city
            }
            
        except Exception as e:
            logger.error(f"Error scraping listing details: {str(e)}")
            return {
                'description': '',
                'phone_number': '',
                'photo_urls': [],
                'state': '',
                'city': ''
            }
    
    def _parse_html_listings(self, html_content, city_domain):
        """Parse HTML response from Craigslist"""
        listings = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all listing elements
        listing_elements = soup.select('.result-info') or soup.select('.cl-static-search-result')
        
        for listing_el in listing_elements:
            try:
                # Extract data from HTML
                title_el = listing_el.select_one('.result-title') or listing_el.select_one('h3 a')
                price_el = listing_el.select_one('.result-price') or listing_el.select_one('.price')
                location_el = listing_el.select_one('.result-hood') or listing_el.select_one('.location')
                
                # Get the title and URL
                title = title_el.text.strip() if title_el else 'No Title'
                url = title_el['href'] if title_el and 'href' in title_el.attrs else ''
                
                # Try to find the listing ID from the URL or element ID
                listing_id = ''
                if url:
                    id_match = re.search(r'/(\d+)\.html', url)
                    if id_match:
                        listing_id = id_match.group(1)
                
                # Get price
                price = price_el.text.strip() if price_el else ''
                
                # Get location
                location = location_el.text.strip() if location_el else ''
                
                # Find image URL if available
                image_url = ''
                gallery_el = soup.select_one(f'[data-pid="{listing_id}"] .result-image') if listing_id else None
                if gallery_el and 'data-ids' in gallery_el.attrs:
                    img_ids = gallery_el['data-ids'].split(',')
                    if img_ids:
                        first_id = img_ids[0].split(':')[1]
                        image_url = f"https://images.craigslist.org/{first_id}_300x300.jpg"
                
                # Get detailed information from the listing page
                details = {}
                if url:
                    details = self._scrape_listing_details(url)
                
                # Create the listing object with all the required fields
                listing = {
                    'listing_id': listing_id,
                    'title': title,
                    'price': price,
                    'location': location,
                    'url': url,
                    'image_url': image_url,
                    'posted_date': datetime.datetime.now().isoformat(),
                    'state': details.get('state', city_domain),
                    'city': details.get('city', location.strip('()') if location else ''),
                    'description': details.get('description', ''),
                    'phone_number': details.get('phone_number', ''),
                    'photo_urls': details.get('photo_urls', [image_url] if image_url else [])
                }
                
                listings.append(listing)
            
            except Exception as e:
                logger.error(f"Error parsing listing: {str(e)}")
                continue
        
        return {
            "city_domain": city_domain,
            "success": True,
            "listings": listings
        }
    
    def scrape_all_cities(self):
        """Scrape all cities in parallel and return results organized by city name"""
        start_time = time.time()
        logger.info("Starting to scrape all Craigslist cities...")
        
        city_domains = [city['domain'] for city in self.get_cities()]
        results_by_city = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            scrape_results = list(executor.map(self.scrape_city, city_domains))
        
        # Organize results by city name
        for result in scrape_results:
            city_domain = result['city_domain']
            city_info = next((city for city in self.get_cities() if city['domain'] == city_domain), None)
            
            if city_info and result['success'] and result['listings']:
                city_name = city_info['name']
                results_by_city[city_name] = result['listings']
        
        elapsed_time = time.time() - start_time
        logger.info(f"Completed scraping all cities in {elapsed_time:.2f} seconds. Found data for {len(results_by_city)} cities.")
        
        return results_by_city
