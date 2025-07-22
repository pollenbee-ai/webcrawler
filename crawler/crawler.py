import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import spacy
from markdownify import markdownify as md
from dateutil.parser import parse as dateparse
from datetime import date
from collections import defaultdict
from . import classifier

nlp = spacy.load("en_core_web_sm")

def crawl_website(start_url, max_pages=10):
    clzifi = classifier("../config.yaml")

    visited = set()
    queue = deque([start_url])

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            visited.add(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            clzifi.classify(text)
            clzifi.dump()

            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])
                if urlparse(full_url).netloc == urlparse(start_url).netloc:
                    queue.append(full_url)

        except Exception as e:
            print(f"Error crawling {url}: {e}")
