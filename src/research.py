import logging
import feedparser

logger = logging.getLogger(__name__)

# Top tech RSS feeds
TECH_RSS_FEEDS = [
    "https://news.ycombinator.com/rss",
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml"
]

def fetch_latest_tech_news():
    """
    Fetches the latest trending tech news item from predefined RSS feeds.
    """
    for feed_url in TECH_RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            if parsed.entries:
                first_entry = parsed.entries[0]
                return {
                    "title": first_entry.get("title", ""),
                    "summary": first_entry.get("summary", first_entry.get("title", "")),
                    "link": first_entry.get("link", "")
                }
        except Exception as e:
            logger.warning(f"Failed to fetch feed {feed_url}: {e}")

    logger.error("No news items retrieved from feeds.")
    return None