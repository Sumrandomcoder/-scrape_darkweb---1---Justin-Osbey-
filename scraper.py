import requests
import time
import random
import json
import re
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import stem.process
import stem.control
from config import TARGET_SITES, DATA_TYPES, CONTENT_FILTERS, TOR_PORT, CONTROL_PORT

class DarkWebScraper:
    def __init__(self):
        self.tor_port = TOR_PORT
        self.control_port = CONTROL_PORT
        self.session = None
        self.ua = UserAgent()
        self.tor_process = None
        
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})')
        self.username_pattern = re.compile(r'@[A-Za-z0-9_]+|username[:\s]+([A-Za-z0-9_]+)', re.IGNORECASE)
        
        self.scraped_data = {
            'emails': set(),
            'usernames': set(),
            'phone_numbers': set(),
            'urls': set(),
            'content': []
        }
    
    def start_tor(self):
        try:
            response = requests.get('http://httpbin.org/ip', 
                                  proxies={'http': f'socks5://127.0.0.1:{self.tor_port}',
                                          'https': f'socks5://127.0.0.1:{self.tor_port}'},
                                  timeout=10)
            print("Tor already running")
            return True
        except:
            print("Starting Tor...")
            try:
                self.tor_process = stem.process.launch_tor_with_config(
                    config={
                        'SocksPort': str(self.tor_port),
                        'ControlPort': str(self.control_port),
                        'ExitNodes': '{us},{ca},{gb}',
                        'StrictNodes': '1',
                    }
                )
                print("Tor started")
                return True
            except Exception as e:
                print(f"Failed to start Tor: {e}")
                return False
    
    def create_session(self):
        self.session = requests.Session()
        self.session.proxies = {
            'http': f'socks5://127.0.0.1:{self.tor_port}',
            'https': f'socks5://127.0.0.1:{self.tor_port}'
        }
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
        self.session.timeout = 30
    
    def renew_identity(self):
        try:
            with stem.control.Controller.from_port(port=self.control_port) as controller:
                controller.authenticate()
                controller.signal(stem.Signal.NEWNYM)
                print("Identity renewed")
                time.sleep(5)
        except Exception as e:
            print(f"Failed to renew identity: {e}")
    
    def make_request(self, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                time.sleep(random.uniform(2, 8))
                self.session.headers['User-Agent'] = self.ua.random
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    print(f"Success: {url}")
                    return response
                elif response.status_code == 429:
                    print("Rate limited, waiting...")
                    time.sleep(random.uniform(30, 60))
                    self.renew_identity()
                else:
                    print(f"HTTP {response.status_code} for {url}")
                    
            except requests.exceptions.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(10, 20))
                    self.renew_identity()
        return None
    
    def filter_content(self, content, filters):
        content_lower = content.lower()
        return any(filter_keyword.lower() in content_lower for filter_keyword in filters)
    
    def extract_data(self, html_content, url):
        soup = BeautifulSoup(html_content, 'lxml')
        text_content = soup.get_text()
        
        emails = set(self.email_pattern.findall(text_content))
        
        phone_matches = self.phone_pattern.findall(text_content)
        phone_numbers = set([''.join(match) for match in phone_matches])
        
        username_matches = self.username_pattern.findall(text_content)
        usernames = set([match for match in username_matches if match])
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            if 'user' in href.lower() or 'profile' in href.lower():
                username = href.split('/')[-1]
                if username and len(username) > 2:
                    usernames.add(username)
        
        return {
            'emails': emails,
            'phone_numbers': phone_numbers,
            'usernames': usernames,
            'url': url,
            'timestamp': time.time(),
            'content_length': len(text_content)
        }
    
    def scrape_site(self, url, filters, max_pages=10):
        print(f"Scraping: {url}")
        
        response = self.make_request(url)
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        if not self.filter_content(soup.get_text(), filters):
            print(f"Content doesn't match filters for {url}")
            return {}
        
        page_data = self.extract_data(response.content, url)
        
        self.scraped_data['emails'].update(page_data['emails'])
        self.scraped_data['usernames'].update(page_data['usernames'])
        self.scraped_data['phone_numbers'].update(page_data['phone_numbers'])
        self.scraped_data['urls'].add(url)
        self.scraped_data['content'].append(page_data)
        
        links = soup.find_all('a', href=True)
        additional_urls = set()
        
        for link in links:
            href = link.get('href')
            if href:
                full_url = urljoin(url, href)
                if full_url not in self.scraped_data['urls'] and len(additional_urls) < max_pages:
                    additional_urls.add(full_url)
        
        for additional_url in list(additional_urls)[:max_pages-1]:
            print(f"Scraping additional: {additional_url}")
            response = self.make_request(additional_url)
            
            if response:
                soup = BeautifulSoup(response.content, 'lxml')
                if self.filter_content(soup.get_text(), filters):
                    page_data = self.extract_data(response.content, additional_url)
                    
                    self.scraped_data['emails'].update(page_data['emails'])
                    self.scraped_data['usernames'].update(page_data['usernames'])
                    self.scraped_data['phone_numbers'].update(page_data['phone_numbers'])
                    self.scraped_data['urls'].add(additional_url)
                    self.scraped_data['content'].append(page_data)
        
        return self.scraped_data
    
    def save_data(self, filename=None):
        if not filename:
            filename = f"scraped_data_{int(time.time())}"
        
        json_data = {
            'emails': list(self.scraped_data['emails']),
            'usernames': list(self.scraped_data['usernames']),
            'phone_numbers': list(self.scraped_data['phone_numbers']),
            'urls': list(self.scraped_data['urls']),
            'content': self.scraped_data['content'],
            'scrape_timestamp': time.time(),
            'total_emails': len(self.scraped_data['emails']),
            'total_usernames': len(self.scraped_data['usernames']),
            'total_phone_numbers': len(self.scraped_data['phone_numbers']),
            'total_urls': len(self.scraped_data['urls'])
        }
        
        with open(f"{filename}.json", 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        with open(f"{filename}_emails.txt", 'w', encoding='utf-8') as f:
            for email in self.scraped_data['emails']:
                f.write(f"{email}\n")
        
        with open(f"{filename}_usernames.txt", 'w', encoding='utf-8') as f:
            for username in self.scraped_data['usernames']:
                f.write(f"{username}\n")
        
        with open(f"{filename}_phone_numbers.txt", 'w', encoding='utf-8') as f:
            for phone in self.scraped_data['phone_numbers']:
                f.write(f"{phone}\n")
        
        print(f"Data saved to {filename}.* files")
    
    def run_scraping(self, target_sites, data_types, filters):
        print("Starting scraping process")
        
        if not self.start_tor():
            print("Failed to start Tor")
            return
        
        self.create_session()
        
        for site in target_sites:
            try:
                print(f"Scraping site: {site}")
                self.scrape_site(site, filters)
                self.renew_identity()
            except Exception as e:
                print(f"Error scraping {site}: {e}")
                continue
        
        self.save_data()
        
        print("Scraping completed!")
        print(f"Total emails: {len(self.scraped_data['emails'])}")
        print(f"Total usernames: {len(self.scraped_data['usernames'])}")
        print(f"Total phone numbers: {len(self.scraped_data['phone_numbers'])}")
        print(f"Total URLs: {len(self.scraped_data['urls'])}")
    
    def cleanup(self):
        if self.tor_process:
            self.tor_process.terminate()
            print("Tor process terminated")

def main():
    config = {
        "target_sites": TARGET_SITES,
        "data_types": DATA_TYPES,
        "filter": CONTENT_FILTERS
    }
    
    scraper = DarkWebScraper()
    
    try:
        scraper.run_scraping(
            target_sites=config["target_sites"],
            data_types=config["data_types"],
            filters=config["filter"]
        )
    except KeyboardInterrupt:
        print("\nScraping interrupted")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()
