import feedparser
import logging
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_html(html_content):
    """Strips HTML tags and returns clean text."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def fetch_feed_articles(feed_url, max_articles=5):
    """Fetches and parses articles from an RSS feed, returning top N articles."""
    articles = []
    try:
        # Use common browser headers to avoid blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(feed_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        if feed.bozo and not feed.entries:
            logger.warning(f"Possible malformed feed XML from {feed_url}: {feed.bozo_exception}")
            
        entries = feed.entries[:max_articles]
        for entry in entries:
            title = entry.get('title', 'No Title')
            
            # Determine body text (content vs. summary vs. description)
            body = ""
            if 'content' in entry and entry.content:
                body = " ".join([clean_html(c.value) for c in entry.content if c.value])
            elif 'summary' in entry:
                body = clean_html(entry.summary)
            elif 'description' in entry:
                body = clean_html(entry.description)
                
            articles.append({
                'title': clean_html(title),
                'body': body,
                'link': entry.get('link', '')
            })
            
    except Exception as e:
        logger.error(f"Error fetching or parsing feed {feed_url}: {str(e)}")
        # Silent skip as requested: log the error and skip silently
        pass
        
    return articles

def fetch_cybersecurity_news():
    """Fetches articles from Cybersecurity RSS feeds."""
    feeds = [
        "https://feeds.feedburner.com/TheHackersNews",
        "https://www.bleepingcomputer.com/feed/",
        "https://feeds.feedburner.com/KrebsOnSecurity"
    ]
    all_articles = []
    for feed in feeds:
        all_articles.extend(fetch_feed_articles(feed))
    return all_articles

def fetch_geopolitical_news():
    """Fetches articles from Geopolitical/War RSS feeds."""
    feeds = [
        "https://feeds.reuters.com/reuters/worldNews",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
    ]
    all_articles = []
    for feed in feeds:
        all_articles.extend(fetch_feed_articles(feed))
    return all_articles

def fetch_general_world_news():
    """Fetches articles from General World RSS feeds."""
    feeds = [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
    ]
    all_articles = []
    for feed in feeds:
        all_articles.extend(fetch_feed_articles(feed))
    return all_articles
