import os
import logging
import datetime
from dotenv import load_dotenv
import pytz
import asyncio


# Load local environment variables from .env if present
load_dotenv()

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Import pipeline components
from fetcher import fetch_cybersecurity_news, fetch_geopolitical_news, fetch_general_world_news
from sports import process_world_cup_briefing
from summariser import summarize_cybersecurity, summarize_geopolitics, summarize_sports, summarize_general_world
from bot import send_briefing_async

async def run_news_briefing_pipeline():
    """Runs the full fetching, summarising, and Telegram sending pipeline."""
    logger.info("Starting daily news briefing pipeline...")
    try:
        # 1. Fetch raw data
        logger.info("Fetching cybersecurity news RSS feeds...")
        cyber_articles = fetch_cybersecurity_news()
        logger.info(f"Retrieved {len(cyber_articles)} cybersecurity articles.")
        
        logger.info("Fetching geopolitical news RSS feeds...")
        geo_articles = fetch_geopolitical_news()
        logger.info(f"Retrieved {len(geo_articles)} geopolitical articles.")
        
        logger.info("Fetching general world news RSS feeds...")
        world_articles = fetch_general_world_news()
        logger.info(f"Retrieved {len(world_articles)} general world articles.")
        
        logger.info("Fetching FIFA World Cup sports scoreboard from ESPN...")
        ist_tz = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.datetime.now(ist_tz)
        sports_data = process_world_cup_briefing(now_ist)
        
        # 2. Summarize using Gemini
        logger.info("Requesting Gemini summary for Cybersecurity...")
        cyber_summary = summarize_cybersecurity(cyber_articles)
        
        logger.info("Requesting Gemini summary for War/Geopolitics...")
        geo_summary = summarize_geopolitics(geo_articles)
        
        logger.info("Requesting Gemini layout for FIFA World Cup...")
        sports_summary = summarize_sports(sports_data)
        
        logger.info("Requesting Gemini summary for General World News...")
        world_summary = summarize_general_world(world_articles)
        
        # 3. Send final briefing to Telegram
        logger.info("Sending news briefing to Telegram...")
        await send_briefing_async(cyber_summary, geo_summary, sports_summary, world_summary)
        logger.info("News briefing pipeline finished successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline execution encountered an error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(run_news_briefing_pipeline())

