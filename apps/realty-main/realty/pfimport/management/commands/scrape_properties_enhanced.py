import os
import re
import time
import json
import datetime
import requests
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class PropertyFinderScraper:
    """Enhanced PropertyFinder scraper with robust error handling and logging."""
    
    def __init__(self, output_dir: str = "/shared-data", log_level: str = "INFO"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.setup_logging(log_level)
        self.setup_session()
        self.stats = {
            'pages_processed': 0,
            'links_found': 0,
            'properties_processed': 0,
            'properties_saved': 0,
            'errors': 0,
            'retries': 0
        }
    
    def setup_logging(self, log_level: str):
        """Setup comprehensive logging system."""
        self.logger = logging.getLogger('propertyfinder_scraper')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = self.output_dir / f"scraper_{datetime.datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def setup_session(self):
        """Setup requests session with retry strategy and robust configuration."""
        self.session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=5,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=2,
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers and cookies
        self.session.headers.update(self.get_headers())
        self.session.cookies.update(self.get_cookies())
    
    def get_headers(self) -> Dict[str, str]:
        """Get randomized headers to avoid detection."""
        return {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        }
    
    def get_cookies(self) -> Dict[str, str]:
        """Get base cookies - in production these should be rotated."""
        return {
            "flagship_user_id": f"scraper_{int(time.time())}",
            "anonymous_user_id": f"scraper_{int(time.time())}",
        }
    
    def safe_request(self, url: str, max_retries: int = 3, timeout: int = 30) -> Optional[requests.Response]:
        """Make a safe HTTP request with comprehensive error handling."""
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Attempting request to {url} (attempt {attempt + 1})")
                
                response = self.session.get(url, timeout=timeout)
                
                # Check for various error conditions
                if response.status_code == 429:
                    wait_time = (attempt + 1) * 10
                    self.logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    self.stats['retries'] += 1
                    continue
                
                if response.status_code >= 400:
                    self.logger.error(f"HTTP {response.status_code} for {url}")
                    if attempt < max_retries - 1:
                        time.sleep((attempt + 1) * 2)
                        continue
                    return None
                
                # Check for captcha or blocking
                if self.is_blocked(response):
                    self.logger.error(f"Detected blocking/captcha for {url}")
                    wait_time = (attempt + 1) * 30
                    self.logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                
                return response
                
            except requests.exceptions.Timeout:
                self.logger.error(f"Timeout for {url} (attempt {attempt + 1})")
                self.stats['errors'] += 1
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 5)
                    continue
            
            except requests.exceptions.ConnectionError:
                self.logger.error(f"Connection error for {url} (attempt {attempt + 1})")
                self.stats['errors'] += 1
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 10)
                    continue
            
            except Exception as e:
                self.logger.error(f"Unexpected error for {url}: {e}")
                self.stats['errors'] += 1
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
                    continue
        
        self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
    
    def is_blocked(self, response: requests.Response) -> bool:
        """Check if the response indicates we're being blocked."""
        text = response.text.lower()
        blocking_indicators = [
            "captcha",
            "blocked",
            "access denied",
            "forbidden",
            "rate limited",
            "too many requests",
            "security check"
        ]
        return any(indicator in text for indicator in blocking_indicators)
    
    def build_page_url(self, base_url: str, page_num: int) -> str:
        """Create URL for specific page number."""
        if "page=" in base_url:
            return re.sub(r"page=\d+", f"page={page_num}", base_url)
        sep = "&" if "?" in base_url else "?"
        return f"{base_url}{sep}page={page_num}"
    
    def extract_links_from_page(self, html: str) -> List[str]:
        """Extract property links from search results page."""
        try:
            soup = BeautifulSoup(html, "lxml")
            section = soup.select_one("[aria-label='Properties']")
            if not section:
                return []
            
            links = []
            for a in section.select("[data-testid='property-card-link']"):
                if a.has_attr("href"):
                    href = a["href"]
                    if not href.startswith("http"):
                        href = f"https://www.propertyfinder.ae{href}"
                    links.append(href)
            
            return links
            
        except Exception as e:
            self.logger.error(f"Error extracting links: {e}")
            return []
    
    def extract_property_data(self, html: str, url: str) -> Optional[Dict]:
        """Extract property data from individual property page."""
        try:
            soup = BeautifulSoup(html, "lxml")
            script = soup.body.find("script")
            if not script or not script.string:
                return None
            
            text = script.string
            idx = text.find("{")
            if idx < 0:
                return None
            
            json_data = json.loads(text[idx:])
            return self.transform_property(json_data, url)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error for {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting property data from {url}: {e}")
            return None
    
    def transform_property(self, data: Dict, url: str) -> Optional[Dict]:
        """Transform raw property data to structured format."""
        try:
            prop = (
                data.get("props", {})
                .get("pageProps", {})
                .get("propertyResult", {})
                .get("property", {})
            )

            if not prop:
                return None

            # Extract basic details with safe access
            property_data = {
                "id": prop.get("id"),
                "url": url,
                "title": prop.get("title"),
                "displayAddress": prop.get("location", {}).get("full_name"),
                "bedrooms": prop.get("bedrooms"),
                "bathrooms": prop.get("bathrooms"),
                "addedOn": prop.get("listed_date"),
                "broker": prop.get("broker", {}).get("name"),
                "agent": prop.get("agent", {}).get("name"),
                "verified": bool(prop.get("is_verified")),
                "reference": prop.get("reference"),
                "brokerLicenseNumber": prop.get("broker", {}).get("license_number"),
                "priceDuration": "rent" if prop.get("isRent") else "sell",
                "propertyType": prop.get("property_type"),
                "price": prop.get("price", {}).get("value"),
                "priceCurrency": prop.get("price", {}).get("currency"),
                "coordinates": {
                    "latitude": prop.get("location", {}).get("coordinates", {}).get("lat"),
                    "longitude": prop.get("location", {}).get("coordinates", {}).get("lon"),
                },
                "size": f"{prop.get('size', {}).get('value', '')} {prop.get('size', {}).get('unit', '')}".strip(),
                "furnishing": prop.get("furnished", "NO").upper(),
                "features": [a.get("name") for a in prop.get("amenities", []) if a.get("name")],
                "description": prop.get("description"),
                "images": [
                    img.get("full") for img in prop.get("images", {}).get("property", [])
                    if img.get("full")
                ],
                "scraped_at": datetime.datetime.now().isoformat(),
            }

            # Validate required fields
            if not property_data.get("id") or not property_data.get("title"):
                self.logger.warning(f"Missing required fields for {url}")
                return None

            return property_data

        except Exception as e:
            self.logger.error(f"Error transforming property data: {e}")
            return None
    
    def save_incremental(self, properties: List[Dict], batch_num: int):
        """Save properties incrementally to avoid data loss."""
        if not properties:
            return
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"properties_batch_{batch_num}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(properties, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved batch {batch_num}: {len(properties)} properties to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving batch {batch_num}: {e}")
    
    def scrape_properties(self, start_page: int, end_page: int, sleep_time: int = 2) -> Dict:
        """Main scraping method with comprehensive error handling."""
        base_url = "https://www.propertyfinder.ae/en/search?l=1&c=2&t=1&fu=0&rp=y&ob=nd&page=220"
        
        self.logger.info(f"Starting scrape: pages {start_page}-{end_page}, sleep={sleep_time}s")
        
        all_links = set()
        all_properties = []
        
        # Phase 1: Collect all property links
        for page in range(start_page, end_page + 1):
            url = self.build_page_url(base_url, page)
            self.logger.info(f"Processing page {page}/{end_page}: {url}")
            
            response = self.safe_request(url)
            if not response:
                self.logger.error(f"Failed to fetch page {page}")
                continue
            
            links = self.extract_links_from_page(response.text)
            if not links:
                self.logger.warning(f"No links found on page {page}")
                if page > start_page + 5:  # Allow some pages without results, then stop
                    self.logger.info("Multiple pages without results, stopping link collection")
                    break
                continue
            
            all_links.update(links)
            self.stats['pages_processed'] += 1
            self.stats['links_found'] += len(links)
            
            self.logger.info(f"Found {len(links)} links on page {page}, total unique: {len(all_links)}")
            
            time.sleep(sleep_time)
        
        # Phase 2: Process all property pages
        self.logger.info(f"Starting to process {len(all_links)} property pages...")
        
        batch_size = 50
        batch_properties = []
        batch_num = 1
        
        for idx, link in enumerate(sorted(all_links), 1):
            self.logger.debug(f"Processing property {idx}/{len(all_links)}: {link}")
            
            response = self.safe_request(link)
            if not response:
                self.stats['errors'] += 1
                continue
            
            property_data = self.extract_property_data(response.text, link)
            if property_data:
                batch_properties.append(property_data)
                all_properties.append(property_data)
                self.stats['properties_processed'] += 1
                
                if idx % 10 == 0:
                    self.logger.info(f"Processed {idx}/{len(all_links)} properties, found {len(all_properties)} valid")
            else:
                self.stats['errors'] += 1
            
            # Save incremental batches
            if len(batch_properties) >= batch_size:
                self.save_incremental(batch_properties, batch_num)
                self.stats['properties_saved'] += len(batch_properties)
                batch_properties = []
                batch_num += 1
            
            time.sleep(sleep_time)
        
        # Save remaining properties
        if batch_properties:
            self.save_incremental(batch_properties, batch_num)
            self.stats['properties_saved'] += len(batch_properties)
        
        # Save final consolidated file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        final_filename = f"properties_final_{timestamp}.json"
        final_filepath = self.output_dir / final_filename
        
        with open(final_filepath, "w", encoding="utf-8") as f:
            json.dump(all_properties, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved final file: {final_filename} with {len(all_properties)} properties")
        
        return {
            'status': 'completed',
            'final_file': str(final_filepath),
            'properties_count': len(all_properties),
            'stats': self.stats
        }


class Command(BaseCommand):
    help = "Enhanced PropertyFinder scraper with robust error handling"

    def add_arguments(self, parser):
        parser.add_argument("start_value", type=int, help="Page start value")
        parser.add_argument("end_value", type=int, help="Page end value")
        parser.add_argument(
            "--sleep",
            type=int,
            default=2,
            help="Sleep time between requests in seconds",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="/shared-data",
            help="Output directory for JSON files",
        )
        parser.add_argument(
            "--log-level",
            type=str,
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            help="Logging level",
        )

    def handle(self, *args, **options):
        start_value = options["start_value"]
        end_value = options["end_value"]
        sleep_time = options["sleep"]
        output_dir = options["output_dir"]
        log_level = options["log_level"]

        self.stdout.write(
            self.style.SUCCESS(
                f"🚀 Starting enhanced PropertyFinder scraper"
            )
        )
        self.stdout.write(f"📄 Pages: {start_value} - {end_value}")
        self.stdout.write(f"⏱️ Sleep time: {sleep_time}s")
        self.stdout.write(f"📁 Output directory: {output_dir}")
        self.stdout.write(f"📝 Log level: {log_level}")

        scraper = PropertyFinderScraper(output_dir=output_dir, log_level=log_level)
        
        try:
            result = scraper.scrape_properties(start_value, end_value, sleep_time)
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Scraping completed successfully!")
            )
            self.stdout.write(f"📊 Properties processed: {result['properties_count']}")
            self.stdout.write(f"📁 Final file: {result['final_file']}")
            self.stdout.write(f"📈 Stats: {result['stats']}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Scraping failed: {e}")
            )
            raise