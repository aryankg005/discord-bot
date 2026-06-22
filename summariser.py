import os
import logging
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_gemini_model(system_instruction):
    """Helper to initialize and retrieve a GenerativeModel instance."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is missing.")
        raise ValueError("GEMINI_API_KEY is not set.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=system_instruction
    )

def summarize_cybersecurity(articles):
    """Summarizes cybersecurity articles. Falls back to raw headlines if API fails."""
    if not articles:
        return "No cybersecurity news available for the last 24 hours."
        
    text_content = ""
    for idx, art in enumerate(articles, 1):
        text_content += f"Article {idx}:\nTitle: {art['title']}\nBody: {art['body']}\n\n"
        
    system_instruction = (
        "You are an expert cybersecurity analyst. Summarize the provided news stories "
        "into a clean daily briefing. Focus on key threats, vulnerabilities, and breaches "
        "disclosed in the last 24 hours. Organize the information logically with clear points. "
        "Do not include any opening greetings, titles, or concluding remarks. Start directly with the content."
        "summarise each topic into 2-4 sentences. use a modern free genz kind of language instead of tough english ones"
    )
    
    try:
        model = _get_gemini_model(system_instruction)
        summary = model.generate_content(text_content).text.strip()
        return summary
    except Exception as e:
        logger.error(f"Gemini cybersecurity summarisation failed: {e}. Using fallback raw headlines.")
        fallback = "⚠️ *Gemini summary unavailable. Showing raw headlines instead:*\n\n"
        for art in articles[:15]:
            fallback += f"• [{art['title']}]({art['link']})\n"
        return fallback

def summarize_geopolitics(articles):
    """Summarizes geopolitical/war articles. Falls back to raw headlines if API fails."""
    if not articles:
        return "No geopolitical news available for the last 24 hours."
        
    text_content = ""
    for idx, art in enumerate(articles, 1):
        text_content += f"Article {idx}:\nTitle: {art['title']}\nBody: {art['body']}\n\n"
        
    system_instruction = (
        "You are an expert geopolitical intelligence analyst. Summarize the provided news stories "
        "into a clean briefing. Highlight active conflicts, major geopolitical developments, casualties, "
        "and territory changes if any. Keep it objective, professional, and clear. "
        "Do not include any opening greetings, titles, or concluding remarks. Start directly with the content."
    )
    
    try:
        model = _get_gemini_model(system_instruction)
        summary = model.generate_content(text_content).text.strip()
        return summary
    except Exception as e:
        logger.error(f"Gemini geopolitics summarisation failed: {e}. Using fallback raw headlines.")
        fallback = "⚠️ *Gemini summary unavailable. Showing raw headlines instead:*\n\n"
        for art in articles[:15]:
            fallback += f"• [{art['title']}]({art['link']})\n"
        return fallback

def summarize_sports(sports_data):
    """Formats World Cup sports data via Gemini. Falls back to manual layout if API fails."""
    if not sports_data or not sports_data.get("has_data", False):
        return "No World Cup matches today"
        
    sub_a = sports_data.get("subpart_a", [])
    sub_b = sports_data.get("subpart_b", [])
    sub_c = sports_data.get("subpart_c", [])
    sub_d = sports_data.get("subpart_d", [])
    
    raw_text = "FIFA WORLD CUP MATCH DATA:\n\n"
    
    raw_text += "Subpart A: Completed Games Today (12:30 AM to 7:00 AM IST):\n"
    if sub_a:
        for m in sub_a:
            raw_text += f"- {m['home_team']} {m['home_score']} vs {m['away_team']} {m['away_score']}. Scorers: {m['scorers'] or 'None listed'}\n"
    else:
        raw_text += "- None\n"
        
    raw_text += "\nSubpart B: Currently Live Games:\n"
    if sub_b:
        for m in sub_b:
            raw_text += f"- {m['home_team']} {m['home_score']} vs {m['away_team']} {m['away_score']}. State: {m['status_detail']}, Time: {m['clock']}\n"
    else:
        raw_text += "- None\n"
        
    raw_text += "\nSubpart C: Upcoming Games Today (After 7:00 AM IST):\n"
    if sub_c:
        for m in sub_c:
            raw_text += f"- {m['home_team']} vs {m['away_team']}. Kickoff IST: {m['kickoff_ist']}\n"
    else:
        raw_text += "- None\n"
        
    raw_text += "\nSubpart D: Tomorrow's Fixtures:\n"
    if sub_d:
        for m in sub_d:
            raw_text += f"- {m['home_team']} vs {m['away_team']}. Kickoff IST: {m['kickoff_ist']}\n"
    else:
        raw_text += "- None\n"
        
    system_instruction = (
        "You are a sports briefing assistant. Format the provided raw football data into a clean, highly readable briefing. "
        "Organize it into 4 sub-parts:\n"
        "1. Completed games today (12:30 AM to 7:00 AM IST) - use score (⚽) emoji.\n"
        "2. Currently live games - use live games (🔴) emoji. If there are none, explicitly state 'No games currently live.'\n"
        "3. Upcoming games today after 7:00 AM IST - use upcoming (📅) emoji.\n"
        "4. Tomorrow's fixtures - use upcoming (📅) emoji.\n\n"
        "Make sure to list scores and scorers (if available) for completed games. Keep the formatting extremely clear and clean. "
        "Do not include any greeting or conversational filler. Start directly with the content. for the upcoming matches, just predict on who will win in a fun way"
    )
    
    try:
        model = _get_gemini_model(system_instruction)
        summary = model.generate_content(raw_text).text.strip()
        return summary
    except Exception as e:
        logger.error(f"Gemini sports summarisation failed: {e}. Using fallback layout.")
        
        fallback = ""
        fallback += "⚽ *Completed Games Today (12:30 AM to 7:00 AM IST):*\n"
        if sub_a:
            for m in sub_a:
                fallback += f"• {m['home_team']} {m['home_score']} - {m['away_score']} {m['away_team']}"
                if m['scorers']:
                    fallback += f"\n  Scorers: {m['scorers']}"
                fallback += "\n"
        else:
            fallback += "• None\n"
            
        fallback += "\n🔴 *Currently Live Games:*\n"
        if sub_b:
            for m in sub_b:
                fallback += f"• {m['home_team']} {m['home_score']} - {m['away_score']} {m['away_team']} ({m['clock']} - {m['status_detail']})\n"
        else:
            fallback += "• No games currently live.\n"
            
        fallback += "\n📅 *Upcoming Games Today (After 7:00 AM IST):*\n"
        if sub_c:
            for m in sub_c:
                fallback += f"• {m['home_team']} vs {m['away_team']} @ {m['kickoff_ist']} IST\n"
        else:
            fallback += "• None\n"
            
        fallback += "\n📅 *Tomorrow's Fixtures:*\n"
        if sub_d:
            for m in sub_d:
                fallback += f"• {m['home_team']} vs {m['away_team']} @ {m['kickoff_ist']} IST\n"
        else:
            fallback += "• None\n"
            
        return fallback

def summarize_general_world(articles):
    """Summarizes general world news into top 10 stories, excluding cybersec and war/geopolitics."""
    if not articles:
        return "No general world news available for the last 24 hours."
        
    text_content = ""
    for idx, art in enumerate(articles, 1):
        text_content += f"Article {idx}:\nTitle: {art['title']}\nBody: {art['body']}\n\n"
        
    system_instruction = (
        "You are an editor for global news. Summarize the provided news stories into the top 10 most important world stories of the morning. "
        "CRITICAL CONSTRAINT: You must exclude any stories that are primarily about cybersecurity (hacking, data breaches, digital vulnerabilities) "
        "or war and active military conflicts (bombings, active battlefront reports, geopolitical troop movements), as those are covered in other sections. "
        "Keep the summaries clean, concise, and structured. "
        "Do not include any opening greetings, titles, or concluding remarks. Start directly with the content."
        "use humour and free lanugage wherever possible, use context , be serious about deaths or similar context"
    )
    
    try:
        model = _get_gemini_model(system_instruction)
        summary = model.generate_content(text_content).text.strip()
        return summary
    except Exception as e:
        logger.error(f"Gemini world news summarisation failed: {e}. Using fallback raw headlines.")
        fallback = "⚠️ *Gemini summary unavailable. Showing raw headlines instead:*\n\n"
        for art in articles[:15]:
            fallback += f"• [{art['title']}]({art['link']})\n"
        return fallback
