#!/usr/bin/env python
"""
USA Cars Data Scraper for Craigslist

This scraper:
1. Processes one subdomain at a time (not all at once to avoid server overload)
2. Tracks scraping status for each subdomain (completed/failed)
3. Extracts: state, city, title, description, phone number, price, photo URLs
4. Follows the URL pattern: https://{SUBDOMAIN}.craigslist.org/search/cta?bundleDuplicates=1&hasPic=1&postedToday=1#search=2~gallery~0
5. Closes the browser between subdomains to prevent server overload
"""

import re
import json
import logging
import time
import datetime
import random
import os
import sys
import traceback
from urllib.parse import urlparse, urljoin

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    StaleElementReferenceException, 
    WebDriverException,
    ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("usa_cars_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# List of all US states and their corresponding Craigslist subdomains
US_STATES = [
    {"name": "Alabama", "domains": ["auburn", "bham", "dothan", "florence", "gadsden", "huntsville", "mobile", "montgomery", "tuscaloosa"]},
    {"name": "Alaska", "domains": ["anchorage", "fairbanks", "kenai", "juneau", "southeast alaska"]},
    {"name": "Arizona", "domains": ["flagstaff", "mohave county", "phoenix", "prescott", "show low", "sierra vista", "tucson", "yuma"]},
    {"name": "Arkansas", "domains": ["fayetteville", "fort smith", "jonesboro", "little rock", "texarkana"]},
    {"name": "California", "domains": ["bakersfield", "chico", "fresno", "gold country", "hanford-corcoran", "humboldt county", "imperial county", "inland empire", "los angeles", "mendocino county", "merced", "modesto", "monterey bay", "orange county", "palm springs", "redding", "sacramento", "san diego", "san francisco bay area", "san luis obispo", "santa barbara", "santa maria", "siskiyou county", "stockton", "susanville", "ventura county", "visalia-tulare", "yuba-sutter"]},
    {"name": "Colorado", "domains": ["boulder", "colorado springs", "denver", "eastern CO", "fort collins", "high rockies", "pueblo", "western slope"]},
    {"name": "Connecticut", "domains": ["eastern CT", "hartford", "new haven", "northwest CT"]},
    {"name": "Delaware", "domains": ["delaware"]},
    {"name": "District of Columbia", "domains": ["washington"]},
    {"name": "Florida", "domains": ["broward county", "daytona beach", "florida keys", "fort lauderdale", "ft myers", "gainesville", "heartland florida", "jacksonville", "lakeland", "miami", "north central FL", "ocala", "okaloosa", "orlando", "panama city", "pensacola", "sarasota-bradenton", "south florida", "space coast", "st augustine", "tallahassee", "tampa bay area", "treasure coast", "palm beach county"]},
    {"name": "Georgia", "domains": ["albany", "athens", "atlanta", "augusta", "brunswick", "columbus", "macon", "northwest GA", "savannah", "statesboro", "valdosta"]},
    {"name": "Hawaii", "domains": ["hawaii"]},
    {"name": "Idaho", "domains": ["boise", "east idaho", "lewiston", "twin falls"]},
    {"name": "Illinois", "domains": ["bloomington-normal", "champaign urbana", "chicago", "decatur", "la salle co", "mattoon-charleston", "peoria", "rockford", "southern illinois", "springfield", "western IL"]},
    {"name": "Indiana", "domains": ["bloomington", "evansville", "fort wayne", "indianapolis", "kokomo", "lafayette", "muncie", "richmond", "south bend", "terre haute"]},
    {"name": "Iowa", "domains": ["ames", "cedar rapids", "des moines", "dubuque", "fort dodge", "iowa city", "mason city", "quad cities", "sioux city", "southeast IA", "waterloo"]},
    {"name": "Kansas", "domains": ["lawrence", "manhattan", "northwest KS", "salina", "southeast KS", "southwest KS", "topeka", "wichita"]},
    {"name": "Kentucky", "domains": ["bowling green", "eastern kentucky", "lexington", "louisville", "owensboro", "western KY"]},
    {"name": "Louisiana", "domains": ["baton rouge", "central louisiana", "houma", "lafayette", "lake charles", "monroe", "new orleans", "shreveport"]},
    {"name": "Maine", "domains": ["maine"]},
    {"name": "Maryland", "domains": ["annapolis", "baltimore", "eastern shore", "frederick", "southern maryland", "western maryland"]},
    {"name": "Massachusetts", "domains": ["boston", "cape cod", "south coast", "western massachusetts", "worcester"]},
    {"name": "Michigan", "domains": ["ann arbor", "battle creek", "central michigan", "detroit metro", "flint", "grand rapids", "holland", "jackson", "kalamazoo", "lansing", "monroe", "muskegon", "northern michigan", "port huron", "saginaw-midland-baycity", "southwest michigan", "the thumb", "upper peninsula"]},
    {"name": "Minnesota", "domains": ["bemidji", "brainerd", "duluth", "mankato", "minneapolis", "rochester", "southwest MN", "st cloud"]},
    {"name": "Mississippi", "domains": ["gulfport", "hattiesburg", "jackson", "meridian", "north mississippi", "southwest MS"]},
    {"name": "Missouri", "domains": ["columbia", "joplin", "kansas city", "kirksville", "lake of the ozarks", "southeast missouri", "springfield", "st joseph", "st louis"]},
    {"name": "Montana", "domains": ["billings", "bozeman", "butte", "great falls", "helena", "kalispell", "missoula", "eastern montana"]},
    {"name": "Nebraska", "domains": ["grand island", "lincoln", "north platte", "omaha", "scottsbluff"]},
    {"name": "Nevada", "domains": ["elko", "las vegas", "reno"]},
    {"name": "New Hampshire", "domains": ["new hampshire"]},
    {"name": "New Jersey", "domains": ["central NJ", "jersey shore", "north jersey", "south jersey"]},
    {"name": "New Mexico", "domains": ["albuquerque", "clovis", "farmington", "las cruces", "roswell", "santa fe"]},
    {"name": "New York", "domains": ["albany", "binghamton", "buffalo", "catskills", "chautauqua", "elmira-corning", "finger lakes", "glens falls", "hudson valley", "ithaca", "long island", "new york city", "oneonta", "plattsburgh-adirondacks", "potsdam-canton-massena", "rochester", "syracuse", "twin tiers NY/PA", "utica-rome-oneida", "watertown"]},
    {"name": "North Carolina", "domains": ["asheville", "boone", "charlotte", "eastern NC", "fayetteville", "greensboro", "hickory", "jacksonville", "outer banks", "raleigh", "wilmington", "winston-salem"]},
    {"name": "North Dakota", "domains": ["bismarck", "fargo", "grand forks", "north dakota"]},
    {"name": "Ohio", "domains": ["akron", "ashtabula", "athens", "chillicothe", "cincinnati", "cleveland", "columbus", "dayton", "lima", "mansfield", "sandusky", "toledo", "tuscarawas co", "youngstown", "zanesville"]},
    {"name": "Oklahoma", "domains": ["lawton", "northwest OK", "oklahoma city", "stillwater", "tulsa"]},
    {"name": "Oregon", "domains": ["bend", "corvallis", "east oregon", "eugene", "klamath falls", "medford-ashland", "oregon coast", "portland", "roseburg", "salem"]},
    {"name": "Pennsylvania", "domains": ["altoona-johnstown", "cumberland valley", "erie", "harrisburg", "lancaster", "lehigh valley", "meadville", "philadelphia", "pittsburgh", "poconos", "reading", "scranton", "state college", "williamsport", "york"]},
    {"name": "Rhode Island", "domains": ["rhode island"]},
    {"name": "South Carolina", "domains": ["charleston", "columbia", "florence", "greenville", "hilton head", "myrtle beach"]},
    {"name": "South Dakota", "domains": ["northeast SD", "pierre", "rapid city", "sioux falls", "south dakota"]},
    {"name": "Tennessee", "domains": ["chattanooga", "clarksville", "cookeville", "jackson", "knoxville", "memphis", "nashville", "tri-cities"]},
    {"name": "Texas", "domains": ["abilene", "amarillo", "austin", "beaumont", "brownsville", "college station", "corpus christi", "dallas", "deep east texas", "del rio", "el paso", "galveston", "houston", "killeen", "laredo", "lubbock", "mcallen", "odessa", "san angelo", "san antonio", "san marcos", "southwest TX", "texoma", "tyler", "victoria", "waco", "wichita falls"]},
    {"name": "Utah", "domains": ["logan", "ogden-clearfield", "provo", "salt lake city", "st george"]},
    {"name": "Vermont", "domains": ["vermont"]},
    {"name": "Virginia", "domains": ["charlottesville", "danville", "fredericksburg", "hampton roads", "harrisonburg", "lynchburg", "new river valley", "richmond", "roanoke", "southwest VA", "winchester"]},
    {"name": "Washington", "domains": ["bellingham", "kennewick-pasco-richland", "moses lake", "olympic peninsula", "pullman", "seattle-tacoma", "skagit", "spokane", "wenatchee", "yakima"]},
    {"name": "West Virginia", "domains": ["charleston", "eastern panhandle", "huntington-ashland", "morgantown", "northern panhandle", "parkersburg-marietta", "southern WV", "west virginia"]},
    {"name": "Wisconsin", "domains": ["appleton-oshkosh-FDL", "eau claire", "green bay", "janesville", "kenosha-racine", "la crosse", "madison", "milwaukee", "northern WI", "sheboygan", "wausau"]},
    {"name": "Wyoming", "domains": ["wyoming"]},
    {"name": "Territories", "domains": ["guam-micronesia", "puerto rico", "U.S. virgin islands"]}
]

# Updated modern user agents for 2025
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Vivaldi/6.5.3206.63',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Brave/1.60.123',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
]

class USACarsScraper:
    """
    Scraper for car/truck listings from Craigslist across all US state subdomains.
    Processes one subdomain at a time to avoid server overload.
    """
    
    def __init__(self, timeout=30, headless=True, max_retries=3, debug=False):
        """
        Initialize the scraper with the given parameters.
        
        Args:
            timeout (int): Timeout for page loads in seconds
            headless (bool): Whether to run the browser in headless mode
            max_retries (int): Maximum number of retries for failed requests
            debug (bool): Whether to enable debug mode
        """
        self.timeout = timeout
        self.headless = headless
        self.max_retries = max_retries
        self.debug = debug
        
        # Initialize results storage
        self.results = []
        
        # Initialize status tracking
        self.domain_status = {}
        
        # Check if Chrome is installed
        self._check_chrome_installed()
    
    def _check_chrome_installed(self):
        """Check if Chrome is installed on the system."""
        try:
            # Try to get Chrome version using webdriver_manager
            from webdriver_manager.core.utils import get_browser_version_from_os
            chrome_version = get_browser_version_from_os("google-chrome")
            if not chrome_version:
                logger.warning("Chrome browser not detected. Please make sure Chrome is installed.")
        except Exception as e:
            logger.warning(f"Error checking Chrome installation: {str(e)}")
    
    def get_random_user_agent(self):
        """Get a random user agent."""
        return random.choice(USER_AGENTS)
    
    def create_driver(self):
        """
        Create and configure a new Chrome WebDriver instance with enhanced anti-detection.
        
        Returns:
            WebDriver: A configured Chrome WebDriver instance
        """
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        # Set a random user agent
        user_agent = self.get_random_user_agent()
        chrome_options.add_argument(f"--user-agent={user_agent}")
        
        # Enhanced anti-detection options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-browser-side-navigation")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        
        # Add language and geolocation to appear more human-like
        chrome_options.add_argument("--lang=en-US,en;q=0.9")
        chrome_options.add_argument("--disable-web-security")
        
        # Memory optimization
        chrome_options.add_argument("--js-flags=--expose-gc")
        chrome_options.add_argument("--aggressive-cache-discard")
        chrome_options.add_argument("--disable-cache")
        chrome_options.add_argument("--disable-application-cache")
        chrome_options.add_argument("--disable-offline-load-stale-cache")
        chrome_options.add_argument("--disk-cache-size=0")
        
        # Add experimental options to avoid detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        try:
            # Create and return the WebDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set page load timeout
            driver.set_page_load_timeout(self.timeout)
            
            # Execute CDP commands to avoid detection
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    // Overwrite the 'navigator.webdriver' property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Overwrite the 'navigator.plugins' property to appear more browser-like
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Overwrite the 'navigator.languages' property
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en', 'es']
                    });
                    
                    // Overwrite the 'window.chrome' property
                    window.chrome = {
                        runtime: {}
                    };
                    
                    // Create a fake notification permission
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                """
            })
            
            # Initialize with a direct US-based URL to avoid location-based redirects
            driver.get("https://www.craigslist.org/about/sites#US")
            
            # Add a cookie to simulate a returning visitor
            driver.add_cookie({
                "name": "cl_b", 
                "value": random.randint(10000000, 99999999).__str__(),
                "domain": ".craigslist.org"
            })
            
            # Set a US-based location preference
            driver.add_cookie({
                "name": "cl_def_hp", 
                "value": "newyork",
                "domain": ".craigslist.org"
            })
            
            return driver
            
        except Exception as e:
            logger.error(f"Error creating WebDriver: {str(e)}")
            raise
    
    def get_all_domains(self):
        """
        Get a list of all Craigslist domains for US states.
        
        Returns:
            list: A list of domain dictionaries with state and domain information
        """
        all_domains = []
        for state in US_STATES:
            state_name = state["name"]
            for domain in state["domains"]:
                all_domains.append({
                    "state": state_name,
                    "domain": domain
                })
        return all_domains
    
    def scrape_all_domains(self, output_file=None, max_domains=None, specific_domains=None):
        """
        Scrape car listings from all US state Craigslist domains.
        
        Args:
            output_file (str, optional): Path to save the results JSON file
            max_domains (int, optional): Maximum number of domains to scrape
            specific_domains (list, optional): List of specific domains to scrape
            
        Returns:
            list: A list of dictionaries with scraped data and status information
        """
        # Get all domains
        all_domains = self.get_all_domains()
        
        # Filter domains if specific ones are requested
        if specific_domains:
            domains_to_scrape = [d for d in all_domains if d["domain"] in specific_domains]
            logger.info(f"Scraping {len(domains_to_scrape)} specified domains")
        elif max_domains:
            domains_to_scrape = all_domains[:max_domains]
            logger.info(f"Scraping first {len(domains_to_scrape)} domains")
        else:
            domains_to_scrape = all_domains
            logger.info(f"Scraping all {len(domains_to_scrape)} domains")
        
        # Initialize results
        self.results = []
        self.domain_status = {}
        
        # Process each domain one at a time
        for i, domain_info in enumerate(domains_to_scrape):
            domain = domain_info["domain"]
            state = domain_info["state"]
            
            logger.info(f"Processing domain {i+1}/{len(domains_to_scrape)}: {domain} ({state})")
            
            try:
                # Scrape the domain
                domain_results = self.scrape_domain(domain, state)
                
                # Add to results
                if domain_results:
                    self.results.append({
                        "domain": domain,
                        "state": state,
                        "status": "completed",
                        "listings": domain_results,
                        "count": len(domain_results),
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    self.domain_status[domain] = "completed"
                    logger.info(f"Successfully scraped {len(domain_results)} listings from {domain}")
                else:
                    self.results.append({
                        "domain": domain,
                        "state": state,
                        "status": "failed",
                        "listings": [],
                        "count": 0,
                        "error": "No listings found",
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    self.domain_status[domain] = "failed"
                    logger.warning(f"No listings found for {domain}")
            except Exception as e:
                logger.error(f"Error scraping {domain}: {str(e)}")
                logger.error(traceback.format_exc())
                
                self.results.append({
                    "domain": domain,
                    "state": state,
                    "status": "failed",
                    "listings": [],
                    "count": 0,
                    "error": str(e),
                    "timestamp": datetime.datetime.now().isoformat()
                })
                self.domain_status[domain] = "failed"
            
            # Save intermediate results
            if output_file:
                self.save_results(output_file)
            
            # Add a delay between domains to avoid overloading the server
            if i < len(domains_to_scrape) - 1:
                delay = random.uniform(5, 10)
                logger.info(f"Waiting {delay:.2f} seconds before processing next domain...")
                time.sleep(delay)
        
        # Save final results
        if output_file:
            self.save_results(output_file)
        
        return self.results
    
    def scrape_domain(self, domain, state):
        """
        Scrape car listings from a specific Craigslist domain.
        
        Args:
            domain (str): The Craigslist domain (e.g., 'newyork')
            state (str): The state name
            
        Returns:
            list: A list of car details dictionaries
        """
        driver = None
        domain_results = []
        
        try:
            # Create a new driver for this domain
            driver = self.create_driver()
            
            # Construct the URL with the specific parameters
            url = f"https://{domain}.craigslist.org/search/cta?bundleDuplicates=1&hasPic=1&postedToday=1#search=2~gallery~0"
            
            logger.info(f"Scraping domain: {domain}, URL: {url}")
            
            # Process the domain
            domain_results = self._process_domain(driver, domain, state, url)
            
            return domain_results
            
        except Exception as e:
            logger.error(f"Error scraping domain {domain}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
            
        finally:
            # Always close the driver when done with this domain
            if driver:
                try:
                    driver.quit()
                    logger.info(f"Closed browser for domain: {domain}")
                except Exception as e:
                    logger.error(f"Error closing driver: {str(e)}")
    
    def _process_domain(self, driver, domain, state, url):
        """
        Process all car listings from a domain.
        
        Args:
            driver (WebDriver): The WebDriver instance
            domain (str): The Craigslist domain
            state (str): The state name
            url (str): The URL to scrape
            
        Returns:
            list: A list of car details dictionaries
        """
        domain_results = []
        processed_links = set()
        
        # Process the first page
        current_page_url = url
        page_num = 1
        
        while current_page_url:
            logger.info(f"Processing page {page_num} for domain {domain}: {current_page_url}")
            
            # Process the current page
            next_page_url, links = self._process_listing_page(driver, current_page_url, domain, processed_links)
            
            # Process each link
            for link in links:
                if link not in processed_links:
                    processed_links.add(link)
                    
                    # Scrape car details
                    car_details = self._scrape_car_details(driver, link, domain, state)
                    
                    if car_details:
                        domain_results.append(car_details)
                        logger.info(f"Scraped details for listing: {car_details.get('title', 'No Title')}")
                    
                    # Add a small delay between listings
                    time.sleep(random.uniform(1, 3))
            
            # Move to the next page
            current_page_url = next_page_url
            
            # Add a small delay between pages
            if current_page_url:
                time.sleep(random.uniform(3, 5))
                page_num += 1
        
        logger.info(f"Finished processing {len(domain_results)} listings for domain {domain}")
        return domain_results
    
    def _process_listing_page(self, driver, page_url, domain, processed_links):
        """
        Process a single listing page.
        
        Args:
            driver (WebDriver): The WebDriver instance
            page_url (str): The URL of the listing page
            domain (str): The Craigslist domain
            processed_links (set): Set of already processed links
            
        Returns:
            tuple: (next_page_url, links_found)
        """
        for retry in range(self.max_retries):
            try:
                logger.info(f"Processing listing page: {page_url} (Attempt {retry + 1}/{self.max_retries})")
                
                # Load the page
                driver.get(page_url)
                
                # Check if we're blocked
                if "blocked" in driver.title.lower() or "403" in driver.title:
                    logger.warning(f"Blocked by Craigslist on attempt {retry + 1}. Retrying with different settings...")
                    
                    # Exponential backoff
                    wait_time = (2 ** retry) + random.uniform(1, 3)
                    logger.info(f"Waiting {wait_time:.2f} seconds before retrying...")
                    time.sleep(wait_time)
                    
                    # Create a new driver with different settings
                    driver.quit()
                    driver = self.create_driver()
                    continue
                
                # Wait for the page to load
                WebDriverWait(driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Add a small delay to ensure JavaScript has loaded
                time.sleep(random.uniform(2, 4))
                
                # Scroll down to load more content
                self._scroll_page(driver)
                
                # Find all car links on the page
                links = self._extract_car_links(driver, processed_links)
                
                # Find the next page link
                next_page_url = self._find_next_page_link(driver, page_url)
                
                # Save debug screenshot if enabled
                if self.debug:
                    timestamp = int(time.time())
                    screenshot_path = f"craigslist_debug_{timestamp}.png"
                    driver.save_screenshot(screenshot_path)
                    logger.debug(f"Saved debug screenshot to {screenshot_path}")
                
                return next_page_url, links
                
            except Exception as e:
                logger.error(f"Error processing listing page {page_url} (Attempt {retry + 1}): {str(e)}")
                logger.error(traceback.format_exc())
                
                # Exponential backoff
                wait_time = (2 ** retry) + random.uniform(1, 3)
                logger.info(f"Waiting {wait_time:.2f} seconds before retrying...")
                time.sleep(wait_time)
        
        # If all retries failed, return empty results
        logger.error(f"All {self.max_retries} attempts to process listing page {page_url} failed")
        return None, []
    
    def _scroll_page(self, driver):
        """
        Scroll down the page to load more content.
        
        Args:
            driver (WebDriver): The WebDriver instance
        """
        # Get the initial page height
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        # Scroll down in increments
        for _ in range(3):  # Scroll 3 times
            # Scroll down
            driver.execute_script(f"window.scrollBy(0, {last_height / 3});")
            
            # Wait for the page to load
            time.sleep(0.5)
        
        # Scroll back to the top
        driver.execute_script("window.scrollTo(0, 0);")
    
    def _extract_car_links(self, driver, processed_links):
        """
        Extract car links from the current page.
        
        Args:
            driver (WebDriver): The WebDriver instance
            processed_links (set): Set of already processed links
            
        Returns:
            list: A list of car links
        """
        links = []
        
        # Updated selectors for 2025 Craigslist
        selectors = [
            ".cl-search-result .titlestring a",
            ".cl-search-result a.posting-title",
            ".gallery-card a.posting-title",
            ".result-title",
            "li.result-row a.result-title",
            "a.titlestring",
            "a.hdrlnk",
            ".cl-static-search-result a",
            ".rows a.posting-title",
            ".title a",
            ".titlestring a"
        ]
        
        for selector in selectors:
            try:
                # Find all elements matching the selector
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    for element in elements:
                        try:
                            href = element.get_attribute("href")
                            if href and "craigslist.org" in href and href not in links and href not in processed_links:
                                links.append(href)
                        except (StaleElementReferenceException, Exception) as e:
                            logger.warning(f"Error getting href from element: {str(e)}")
                    
                    # If we found links, no need to try other selectors
                    if links:
                        break
            except Exception as e:
                logger.warning(f"Error finding elements with selector '{selector}': {str(e)}")
        
        # If no links found with CSS selectors, try to find them with XPath
        if not links:
            try:
                # Find all anchor elements with href containing "/d/"
                elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/d/')]")
                
                for element in elements:
                    try:
                        href = element.get_attribute("href")
                        if href and "craigslist.org" in href and href not in links and href not in processed_links:
                            links.append(href)
                    except (StaleElementReferenceException, Exception) as e:
                        logger.warning(f"Error getting href from element: {str(e)}")
            except Exception as e:
                logger.warning(f"Error finding elements with XPath: {str(e)}")
        
        # If still no links, try to extract from page source
        if not links:
            try:
                page_source = driver.page_source
                href_matches = re.findall(r'href="(https://[^"]+\.craigslist\.org/[^"]+/d/[^"]+)"', page_source)
                for href in href_matches:
                    if href not in links and href not in processed_links:
                        links.append(href)
            except Exception as e:
                logger.warning(f"Error extracting links from page source: {str(e)}")
        
        logger.info(f"Found {len(links)} new car links")
        return links
    
    def _find_next_page_link(self, driver, current_url):
        """
        Find the next page link.
        
        Args:
            driver (WebDriver): The WebDriver instance
            current_url (str): The current page URL
            
        Returns:
            str: The URL of the next page, or None if there is no next page
        """
        # Try different selectors for the next page link
        next_page_selectors = [
            ".cl-pagination a.cl-page-next",
            ".cl-pagination a.next",
            ".paginator a.next",
            ".paginator a.nextpage",
            ".paginator-next",
            "a.button.next",
            "a.next",
            "a[title='next page']",
            "a[rel='next']",
            "a.next-page"
        ]
        
        for selector in next_page_selectors:
            try:
                next_page_element = driver.find_element(By.CSS_SELECTOR, selector)
                next_page_url = next_page_element.get_attribute("href")
                
                if next_page_url and next_page_url != current_url:
                    return next_page_url
            except (NoSuchElementException, StaleElementReferenceException):
                continue
            except Exception as e:
                logger.warning(f"Error finding next page link with selector '{selector}': {str(e)}")
        
        # If no next page link found with CSS selectors, try to find it with XPath
        try:
            # Find all anchor elements with text containing "next" or ">"
            elements = driver.find_elements(By.XPATH, "//a[contains(text(), 'next') or contains(text(), '>') or contains(@class, 'next')]")
            
            for element in elements:
                try:
                    next_page_url = element.get_attribute("href")
                    
                    if next_page_url and next_page_url != current_url:
                        return next_page_url
                except (StaleElementReferenceException, Exception) as e:
                    logger.warning(f"Error getting href from next page element: {str(e)}")
        except Exception as e:
            logger.warning(f"Error finding next page link with XPath: {str(e)}")
        
        # If still no next page link, try to extract from page source
        try:
            page_source = driver.page_source
            
            # Look for next page link in the page source
            next_page_matches = re.findall(r'href="([^"]+)"[^>]*>(?:next|&gt;|next page)', page_source, re.IGNORECASE)
            
            if next_page_matches:
                next_page_url = next_page_matches[0]
                
                # Make sure the URL is absolute
                if not next_page_url.startswith("http"):
                    next_page_url = urljoin(current_url, next_page_url)
                
                if next_page_url and next_page_url != current_url:
                    return next_page_url
        except Exception as e:
            logger.warning(f"Error extracting next page link from page source: {str(e)}")
        
        # If no next page link found, return None
        return None
    
    def _scrape_car_details(self, driver, url, domain, state):
        """
        Scrape detailed information from an individual car listing page.
        
        Args:
            driver (WebDriver): The WebDriver instance
            url (str): The URL of the car listing
            domain (str): The Craigslist domain
            state (str): The state name
            
        Returns:
            dict: A dictionary with car details or None if the listing should be skipped
        """
        for retry in range(self.max_retries):
            try:
                logger.info(f"Scraping detailed listing: {url} (Attempt {retry + 1}/{self.max_retries})")
                
                # Load the page
                driver.get(url)
                
                # Check if we're blocked
                if "blocked" in driver.title.lower() or "403" in driver.title:
                    logger.warning(f"Blocked by Craigslist on attempt {retry + 1}. Retrying with different settings...")
                    
                    # Exponential backoff
                    wait_time = (2 ** retry) + random.uniform(1, 3)
                    logger.info(f"Waiting {wait_time:.2f} seconds before retrying...")
                    time.sleep(wait_time)
                    
                    # Create a new driver with different settings
                    driver.quit()
                    driver = self.create_driver()
                    continue
                
                # Wait for the page to load
                WebDriverWait(driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Add a small delay to ensure JavaScript has loaded
                time.sleep(random.uniform(2, 4))
                
                # Scroll down a bit to load more content
                driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(1)
            
                # Extract basic information
                title = ""
                try:
                    # Updated title selectors for 2025
                    title_selectors = [
                        "h1.postingtitle", 
                        "span.postingtitletext", 
                        "h1 span.titlestring",
                        "h1.title",
                        "h2.postingtitle",
                        ".title h2",
                        ".title span",
                        "span.label", 
                        "a.cl-app-anchor.text-only.posting-title span.label"
                    ]
                    
                    for selector in title_selectors:
                        try:
                            title_el = driver.find_element(By.CSS_SELECTOR, selector)
                            title = title_el.text.strip()
                            if title:
                                break
                        except NoSuchElementException:
                            continue
                except Exception as e:
                    logger.warning(f"Error extracting title: {str(e)}")
                
                if not title:
                    # Try to extract title from page title
                    try:
                        page_title = driver.title
                        if page_title and "craigslist" in page_title.lower():
                            title_parts = page_title.split(" - ")
                            if len(title_parts) > 1:
                                title = title_parts[0].strip()
                    except Exception:
                        pass
                
                if not title:
                    title = "No Title"
                
                # Extract price
                price = ""
                try:
                    price_selectors = [
                        "span.price", 
                        ".price", 
                        "span.priceinfo", 
                        ".meta-line .priceinfo"
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_el = driver.find_element(By.CSS_SELECTOR, selector)
                            price = price_el.text.strip()
                            if price:
                                break
                        except NoSuchElementException:
                            continue
                except Exception as e:
                    logger.warning(f"Error extracting price: {str(e)}")
            
                # Extract description
                description = ""
                try:
                    description_selectors = [
                        "#postingbody",
                        ".posting-body",
                        ".posting-description",
                        ".description"
                    ]
                    
                    for selector in description_selectors:
                        try:
                            description_el = driver.find_element(By.CSS_SELECTOR, selector)
                            description = description_el.text.strip()
                            if description:
                                # Remove "QR Code Link to This Post" text if present
                                description = re.sub(r'QR Code Link to This Post\s*', '', description).strip()
                                break
                        except NoSuchElementException:
                            continue
                except Exception as e:
                    logger.warning(f"Error extracting description: {str(e)}")
            
                # Extract all image URLs
                photo_urls = []
                
                # Method 1: Try different selectors for images
                image_selectors = [
                    ".gallery .swipe img", 
                    "#thumbs .thumb img", 
                    ".gallery-image", 
                    ".swipe-wrap img", 
                    ".swipe-wrap div[data-index] img",
                    ".gallery-image img",
                    ".slide img",
                    ".carousel img"
                ]
                
                for selector in image_selectors:
                    try:
                        images = driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        if images:
                            for img in images:
                                try:
                                    img_url = img.get_attribute("src")
                                    if img_url:
                                        # Convert thumbnail URL to full-size image URL
                                        img_url = re.sub(r'_\d+x\d+\.jpg', '_600x450.jpg', img_url)
                                        if img_url not in photo_urls:  # Avoid duplicates
                                            photo_urls.append(img_url)
                                except Exception as e:
                                    logger.warning(f"Error extracting image URL: {str(e)}")
                            
                            # If we found images, no need to try other selectors
                            if photo_urls:
                                break
                    except Exception as e:
                        logger.warning(f"Error finding images with selector '{selector}': {str(e)}")
                
                # Method 2: Look for image data in JavaScript variables
                if not photo_urls:
                    try:
                        # Get the page source
                        page_source = driver.page_source
                        
                        # Look for image IDs in JavaScript
                        img_list_match = re.search(r'var imgList = \[(.*?)\]', page_source, re.DOTALL)
                        if img_list_match:
                            img_list_str = img_list_match.group(1)
                            img_ids = re.findall(r'"([^"]+)"', img_list_str)
                            for img_id in img_ids:
                                img_url = f"https://images.craigslist.org/{img_id}_600x450.jpg"
                                photo_urls.append(img_url)
                    except Exception as e:
                        logger.warning(f"Error extracting image URLs from JavaScript: {str(e)}")
                
                # Method 3: If still no images found, try to find them in the page source
                if not photo_urls:
                    try:
                        # Get the page source
                        page_source = driver.page_source
                        
                        # Look for image URLs in the page source
                        img_urls = re.findall(r'https://images\.craigslist\.org/[^"\']+\.jpg', page_source)
                        for img_url in img_urls:
                            # Convert to full-size image URL
                            img_url = re.sub(r'_\d+x\d+\.jpg', '_600x450.jpg', img_url)
                            if img_url not in photo_urls:
                                photo_urls.append(img_url)
                    except Exception as e:
                        logger.warning(f"Error extracting image URLs from page source: {str(e)}")
                
                # Try to extract phone number from the description
                phone_number = ''
                phone_matches = re.findall(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', description)
                if phone_matches:
                    phone_number = phone_matches[0]
                
                # Extract city from URL path or location
                city = ''
                path_parts = url.split('/')
                if len(path_parts) > 4:
                    # Try to extract from URL path (e.g., /lgi/ctd/d/lynbrook-...)
                    city_part = path_parts[4] if len(path_parts) > 4 else ''
                    if city_part:
                        city_match = re.match(r'([a-zA-Z\-]+)', city_part)
                        if city_match:
                            city = city_match.group(1).replace('-', ' ').title()
                
                # Extract location
                location = ''
                try:
                    location_selectors = [
                        ".postingtitletext .price + small", 
                        ".postinginfos .location", 
                        ".meta-line .meta",
                        ".mapaddress",
                        ".mapbox .viewposting",
                        ".postinginfo .location"
                    ]
                    
                    for selector in location_selectors:
                        try:
                            location_el = driver.find_element(By.CSS_SELECTOR, selector)
                            location = location_el.text.strip()
                            if location:
                                # Try to extract city from location if not already found
                                if not city and ',' in location:
                                    city = location.split(',')[0].strip()
                                break
                        except NoSuchElementException:
                            continue
                except Exception as e:
                    logger.warning(f"Error extracting location: {str(e)}")
                
                # Extract listing ID
                listing_id = ''
                id_match = re.search(r'/(\d+)\.html', url)
                if id_match:
                    listing_id = id_match.group(1)
                
                # Format the results
                car_details = {
                    "url": url,
                    "title": title,
                    "price": price,
                    "description": description,
                    "photo_urls": photo_urls,
                    "phone_number": phone_number,
                    "state": state,
                    "city": city or domain,  # Use domain as fallback if city not found
                    "location": location,
                    "listing_id": listing_id,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                return car_details
                
            except Exception as e:
                logger.error(f"Error scraping {url} (Attempt {retry + 1}): {str(e)}")
                logger.error(traceback.format_exc())
                
                # Exponential backoff
                wait_time = (2 ** retry) + random.uniform(1, 3)
                logger.info(f"Waiting {wait_time:.2f} seconds before retrying...")
                time.sleep(wait_time)
        
        # If all retries failed, return None
        logger.error(f"All {self.max_retries} attempts to scrape {url} failed")
        return None
    
    def save_results(self, output_file):
        """
        Save the results to a JSON file.
        
        Args:
            output_file (str): Path to save the results JSON file
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving results to {output_file}: {str(e)}")
    
    def get_domain_status(self):
        """
        Get the status of all domains.
        
        Returns:
            dict: A dictionary with domain names as keys and status as values
        """
        return self.domain_status

def main():
    """Main function to run the scraper from the command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='USA Cars Data Scraper for Craigslist')
    parser.add_argument('--output', type=str, default=None, help='Output file path (default: auto-generated filename)')
    parser.add_argument('--max-domains', type=int, default=None, help='Maximum number of domains to scrape (default: all)')
    parser.add_argument('--domains', nargs='+', help='List of specific domains to scrape (e.g., newyork chicago)')
    parser.add_argument('--no-headless', action='store_true', help='Run the browser in non-headless mode (visible browser windows)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout for page loads in seconds (default: 30)')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum number of retries for failed requests (default: 3)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (save screenshots)')
    
    args = parser.parse_args()
    
    # Generate output filename if not provided
    if args.output is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"usa_cars_data_{timestamp}.json"
    
    # Create and run the scraper
    scraper = USACarsScraper(
        timeout=args.timeout,
        headless=not args.no_headless,
        max_retries=args.max_retries,
        debug=args.debug
    )
    
    scraper.scrape_all_domains(
        output_file=args.output,
        max_domains=args.max_domains,
        specific_domains=args.domains
    )
    
    # Print summary
    domain_status = scraper.get_domain_status()
    completed_count = sum(1 for status in domain_status.values() if status == "completed")
    failed_count = sum(1 for status in domain_status.values() if status == "failed")
    
    print(f"\nScraping completed!")
    print(f"Total domains processed: {len(domain_status)}")
    print(f"Successful domains: {completed_count}")
    print(f"Failed domains: {failed_count}")
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()
