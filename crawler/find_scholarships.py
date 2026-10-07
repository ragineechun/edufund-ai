import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging

# Simple logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleScholarshipFinder:
    def __init__(self, target_count=20):
        """
        Simple scholarship finder
        
        Args:
            target_count: Stop after finding this many scholarships
        """
        self.target_count = target_count
        self.scholarships = []
        
        # ========== ADD YOUR VERIFIED LINKS HERE ==========
        # Just add any scholarship website URLs you want to crawl
        self.platforms = [
            {
                'name': 'Scholars4Dev',
                'url': 'https://www.scholars4dev.com/',
                'type': 'homepage'
            },
            {
                'name': 'Opportunity Desk', 
                'url': 'https://opportunitydesk.org/',
                'type': 'homepage'
            },
            {
                'name': 'MLH Fellowship',
                'url': 'https://fellowship.mlh.io/',
                'type': 'direct'
            },
            {
                'name': 'GitHub Education',
                'url': 'https://education.github.com/',
                'type': 'direct'
            }
        ]
        
        
        # Also add direct scholarship URLs if you have them
        self.direct_urls = [
          'https://www.vidyasaarathi.co.in/Vidyasaarathi/scholarship',
          'https://www.buddy4study.com/article/',
          'https://bigfuture.collegeboard.org/scholarship-search'
          
            # Add direct scholarship page URLs here
            # 'https://example.com/scholarship-page',
        ]
        
        # Headers to look like a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def should_stop(self):
        """Check if we've found enough scholarships"""
        return len(self.scholarships) >= self.target_count
    
    def fetch_page(self, url, timeout=10):
        """Fetch a webpage"""
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def extract_scholarship_links(self, soup, base_url):
        """Find links that look like scholarships"""
        links = []
        
        # Keywords that indicate a scholarship page
        keywords = ['scholarship', 'fellowship', 'grant', 'award', 'funding']
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().lower()
            full_url = urljoin(base_url, href)
            
            # Check if this link looks like a scholarship
            if any(keyword in href.lower() or keyword in text for keyword in keywords):
                links.append({
                    'title': link.get_text(strip=True)[:100],
                    'url': full_url
                })
        
        return links
    
    def parse_scholarship_page(self, soup, url):
        """Extract detailed info from a scholarship page"""
        scholarship = {
            'title': '',
            'organization': '',
            'amount': '',
            'deadline': '',
            'description': '',
            'eligibility': '',
            'url': url,
            'found_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Get title
        title_tag = soup.find('h1') or soup.find('title')
        if title_tag:
            scholarship['title'] = title_tag.get_text(strip=True)[:150]
        
        # Get description (look for common content areas)
        content_areas = soup.find_all(['p', 'div'], class_=re.compile(r'content|description|entry', re.I))
        for area in content_areas[:3]:
            text = area.get_text(strip=True)
            if len(text) > 100:
                scholarship['description'] = text[:500]
                break
        
        # Extract deadline using patterns
        page_text = soup.get_text()
        deadline_patterns = [
            r'deadline[:\s]+([^.\n]+)',
            r'application deadline[:\s]+([^.\n]+)',
            r'closing date[:\s]+([^.\n]+)',
            r'due date[:\s]+([^.\n]+)'
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                scholarship['deadline'] = match.group(1).strip()[:100]
                break
        
        # Extract amount/value
        amount_match = re.search(r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?', page_text)
        if amount_match:
            scholarship['amount'] = amount_match.group()
        
        # Extract organization (look for common patterns)
        org_match = re.search(r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', page_text[:500])
        if org_match:
            scholarship['organization'] = org_match.group(1)
        
        return scholarship
    
    def add_scholarship(self, scholarship):
        """Add a scholarship and return True if target reached"""
        if scholarship['title'] and scholarship['url']:
            # Avoid duplicates
            if not any(s['url'] == scholarship['url'] for s in self.scholarships):
                self.scholarships.append(scholarship)
                logger.info(f"✓ Found {len(self.scholarships)}/{self.target_count}: {scholarship['title'][:50]}")
                return self.should_stop()
        return False
    
    def crawl_platform(self, platform):
        """Crawl a single platform"""
        logger.info(f"Crawling: {platform['name']} ({platform['url']})")
        
        # Fetch the page
        response = self.fetch_page(platform['url'])
        if not response:
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract scholarship links
        links = self.extract_scholarship_links(soup, platform['url'])
        logger.info(f"Found {len(links)} potential scholarship links on {platform['name']}")
        
        # Visit each link to get details
        for link in links[:10]:  # Limit to first 10 links per site
            if self.should_stop():
                return True
            
            logger.info(f"  Getting details: {link['title'][:40]}...")
            
            # Fetch the scholarship detail page
            detail_response = self.fetch_page(link['url'], timeout=8)
            if detail_response:
                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                scholarship = self.parse_scholarship_page(detail_soup, link['url'])
                
                # Add platform name if organization not found
                if not scholarship['organization']:
                    scholarship['organization'] = platform['name']
                
                # Add title from link if not found
                if not scholarship['title']:
                    scholarship['title'] = link['title']
                
                should_stop = self.add_scholarship(scholarship)
                if should_stop:
                    return True
            
            # Be polite - wait between requests
            time.sleep(1)
        
        return self.should_stop()
    
    def add_direct_scholarships(self):
        """Add scholarships from direct URLs you provide"""
        for url in self.direct_urls:
            if self.should_stop():
                return True
            
            logger.info(f"Checking direct URL: {url}")
            response = self.fetch_page(url)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')
                scholarship = self.parse_scholarship_page(soup, url)
                should_stop = self.add_scholarship(scholarship)
                if should_stop:
                    return True
        
        return False
    
    def add_verified_scholarships(self):
        """Add known scholarships that are always open"""
        # You can add more verified scholarships here
        verified = [
            {
                'title': 'Google Summer of Code',
                'organization': 'Google',
                'amount': '$1500-$6000 stipend',
                'deadline': 'April 2026',
                'description': 'Remote open source contribution program for students',
                'url': 'https://summerofcode.withgoogle.com/'
            },
            {
                'title': 'GitHub Student Developer Pack',
                'organization': 'GitHub',
                'amount': 'Free developer tools',
                'deadline': 'Always open',
                'description': 'Free access to professional developer tools for students',
                'url': 'https://education.github.com/pack'
            },
            {
                'title': 'AWS Educate',
                'organization': 'Amazon',
                'amount': '$100-$200 cloud credits',
                'deadline': 'Always open',
                'description': 'Cloud computing resources and learning for students',
                'url': 'https://aws.amazon.com/education/awseducate/'
            },
            {
                'title': 'Microsoft Learn Student Ambassadors',
                'organization': 'Microsoft',
                'amount': 'Resources & mentorship',
                'deadline': 'Rolling',
                'description': 'Program for student leaders passionate about technology',
                'url': 'https://studentambassadors.microsoft.com/'
            }
        ]
        
        for sch in verified:
            if self.should_stop():
                return True
            sch['found_date'] = datetime.now().strftime('%Y-%m-%d')
            should_stop = self.add_scholarship(sch)
            if should_stop:
                return True
        
        return False
    
    def run(self):
        """Run the crawler"""
        print("\n" + "="*70)
        print(f"🎓 SIMPLE SCHOLARSHIP FINDER")
        print(f"Target: {self.target_count} scholarships")
        print("="*70 + "\n")
        
        # Step 1: Add verified scholarships first (fastest)
        logger.info("Adding verified scholarships...")
        if self.add_verified_scholarships():
            self.save_results()
            self.display_results()
            return self.scholarships
        
        # Step 2: Check direct URLs
        if self.direct_urls:
            logger.info("Checking direct scholarship URLs...")
            if self.add_direct_scholarships():
                self.save_results()
                self.display_results()
                return self.scholarships
        
        # Step 3: Crawl each platform
        for platform in self.platforms:
            if self.should_stop():
                break
            self.crawl_platform(platform)
            time.sleep(2)  # Wait between platforms
        
        # Save results
        self.save_results()
        self.display_results()
        
        return self.scholarships
    
    def save_results(self):
        """Save to CSV file"""
        if self.scholarships:
            filename = f"scholarships_{len(self.scholarships)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df = pd.DataFrame(self.scholarships)
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info(f"💾 Saved to: {filename}")
            return filename
        return None
    
    def display_results(self):
        """Display found scholarships"""
        print("\n" + "="*70)
        print(f"RESULTS: Found {len(self.scholarships)} Scholarships")
        print("="*70)
        
        if not self.scholarships:
            print("\n❌ No scholarships found.")
            return
        
        for i, sch in enumerate(self.scholarships[:self.target_count], 1):
            print(f"\n{i}. {sch.get('title', 'No title')}")
            print(f"   🏢 {sch.get('organization', 'Not specified')}")
            if sch.get('amount'):
                print(f"   💰 {sch.get('amount')}")
            if sch.get('deadline'):
                print(f"   📅 {sch.get('deadline')}")
            if sch.get('description'):
                desc = sch.get('description')[:120]
                print(f"   📝 {desc}{'...' if len(sch.get('description', '')) > 120 else ''}")
            print(f"   🔗 {sch.get('url')}")
        
        print("\n" + "="*70)
        if len(self.scholarships) >= self.target_count:
            print(f"✅ SUCCESS! Found {len(self.scholarships)} scholarships (target reached)")
        else:
            print(f"⚠️ Found {len(self.scholarships)} out of {self.target_count} target")
        print("="*70)


# Quick run function
def quick_find(target=20):
    """Quick function to find scholarships"""
    finder = SimpleScholarshipFinder(target_count=target)
    return finder.run()


if __name__ == "__main__":
    # Just run it!
    # Change the number to how many scholarships you want
    scholarships = quick_find(target=20)
    
    # Or customize it
    # finder = SimpleScholarshipFinder(target_count=15)
    # finder.platforms.append({'name': 'Your Site', 'url': 'https://yoursite.com', 'type': 'homepage'})
    # scholarships = finder.run()