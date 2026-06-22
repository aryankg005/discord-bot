import os
import logging
import requests
import asyncio
from telegram import Bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def split_message(text, limit=2000):
    """Splits a long text into chunks of maximum size `limit` without cutting lines if possible."""
    if len(text) <= limit:
        return [text]
        
    chunks = []
    lines = text.split("\n")
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 > limit:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            # Handle extremely long single lines
            if len(line) > limit:
                for i in range(0, len(line), limit):
                    chunks.append(line[i:i+limit])
            else:
                current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line
                
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

async def send_message_safe_telegram(bot, chat_id, text):
    """Sends a Telegram message, falling back to plain text if Markdown parsing fails."""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info("Telegram message sent successfully with Markdown parse mode.")
    except Exception as e:
        logger.warning(f"Failed to send with Markdown: {e}. Retrying without markdown parse mode.")
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=None
            )
            logger.info("Telegram message sent successfully without parse mode.")
        except Exception as ex:
            logger.error(f"Failed to send Telegram message even without parse mode: {ex}")
            raise ex

async def send_to_telegram_async(cyber_summary, geo_summary, sports_summary, world_summary):
    """Formats and sends the briefing to the configured Telegram chat."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    bot = Bot(token=token)
    
    sec_cyber = f"*🔐 CYBERSECURITY*\n\n{cyber_summary}"
    sec_geo = f"*⚔️ WAR & GEOPOLITICS*\n\n{geo_summary}"
    sec_sports = f"*⚽ FIFA WORLD CUP 2026*\n\n{sports_summary}"
    sec_world = f"*🌍 WORLD NEWS*\n\n{world_summary}"
    
    sections = [sec_cyber, sec_geo, sec_sports, sec_world]
    combined_message = "\n\n".join(sections)
    
    if len(combined_message) <= 4096:
        await send_message_safe_telegram(bot, chat_id, combined_message)
    else:
        logger.info("Telegram briefing exceeds 4096 limit. Sending in 4 separate messages.")
        for section in sections:
            await send_message_safe_telegram(bot, chat_id, section)

async def send_to_discord_async(cyber_summary, geo_summary, sports_summary, world_summary):
    """Formats and sends the briefing to the configured Discord channel via Webhook."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    
    # Discord markdown uses ** for bold
    sec_cyber = f"**🔐 CYBERSECURITY**\n\n{cyber_summary}"
    sec_geo = f"**⚔️ WAR & GEOPOLITICS**\n\n{geo_summary}"
    sec_sports = f"**⚽ FIFA WORLD CUP 2026**\n\n{sports_summary}"
    sec_world = f"**🌍 WORLD NEWS**\n\n{world_summary}"
    
    sections = [sec_cyber, sec_geo, sec_sports, sec_world]
    combined_message = "\n\n".join(sections)
    
    # Discord limit is 2000 characters
    if len(combined_message) <= 2000:
        chunks = [combined_message]
    else:
        logger.info("Discord briefing exceeds 2000 limit. Splitting into sections/chunks.")
        chunks = []
        for sec in sections:
            chunks.extend(split_message(sec, limit=2000))
            
    # Send chunks to Discord Webhook
    for chunk in chunks:
        try:
            loop = asyncio.get_event_loop()
            
            def send_chunk(c):
                response = requests.post(
                    webhook_url,
                    json={"content": c},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                response.raise_for_status()
                return response

            await loop.run_in_executor(None, send_chunk, chunk)
            logger.info("Discord Webhook message chunk sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send message chunk to Discord Webhook: {e}")

async def send_briefing_async(cyber_summary, geo_summary, sports_summary, world_summary):
    """
    Orchestrates sending the briefing. Delivers to Telegram if configured,
    and to Discord Webhook if configured. At least one must be set.
    """
    telegram_configured = bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))
    discord_configured = bool(os.environ.get("DISCORD_WEBHOOK_URL"))
    
    if not telegram_configured and not discord_configured:
        logger.error("Neither Telegram nor Discord webhook environment variables are set.")
        raise ValueError("No destination channels (Telegram or Discord) are configured.")
        
    if telegram_configured:
        logger.info("Telegram configuration detected. Delivering briefing to Telegram...")
        await send_to_telegram_async(cyber_summary, geo_summary, sports_summary, world_summary)
        
    if discord_configured:
        logger.info("Discord configuration detected. Delivering briefing to Discord Webhook...")
        await send_to_discord_async(cyber_summary, geo_summary, sports_summary, world_summary)
