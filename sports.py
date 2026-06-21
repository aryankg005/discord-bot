import requests
import logging
from datetime import datetime, timedelta
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_sports_data(run_date=None):
    """Fetches the FIFA World Cup scoreboard JSON from ESPN API for a date range around run_date."""
    if run_date is None:
        ist_tz = pytz.timezone("Asia/Kolkata")
        run_date = datetime.now(ist_tz).date()
        
    yesterday = run_date - timedelta(days=1)
    tomorrow = run_date + timedelta(days=1)
    date_str = f"{yesterday.strftime('%Y%m%d')}-{tomorrow.strftime('%Y%m%d')}"
    
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={date_str}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching ESPN sports data: {str(e)}")
        return None

def parse_scorers(competition):
    """Parses goal scorers from the competition details if available in ESPN API."""
    scorers = []
    details = competition.get("details", [])
    if not details:
        return ""
        
    for detail in details:
        detail_type = detail.get("type", {})
        if detail_type.get("name") in ["Goal", "Own Goal", "Penalty Goal"]:
            clock_val = detail.get("clock", {}).get("displayValue", "")
            athletes = detail.get("athletesInvolved", [])
            
            athlete_names = [a.get("displayName", "") for a in athletes if a.get("displayName")]
            if athlete_names:
                scorer_name = athlete_names[0]
                if clock_val:
                    scorers.append(f"{scorer_name} ({clock_val})")
                else:
                    scorers.append(scorer_name)
                    
    if scorers:
        return ", ".join(scorers)
    return ""

def process_world_cup_briefing(run_datetime_ist=None):
    """
    Fetches matches from ESPN API and categorizes them into Sub-parts A, B, C, D
    using Asia/Kolkata (IST) timezone.
    """
    if run_datetime_ist is None:
        ist_tz = pytz.timezone("Asia/Kolkata")
        run_datetime_ist = datetime.now(ist_tz)
    
    run_date = run_datetime_ist.date()
    tomorrow_date = (run_datetime_ist + timedelta(days=1)).date()
    
    data = fetch_sports_data(run_date)
    if not data or "events" not in data or not data["events"]:
        return {
            "has_data": False,
            "briefing": "No World Cup matches today"
        }
        
    events = data["events"]
    
    subpart_a = []  # Completed games today (12:30 AM to 7:00 AM IST)
    subpart_b = []  # Currently live games
    subpart_c = []  # Upcoming today after 7:00 AM IST
    subpart_d = []  # Tomorrow's fixtures
    
    # Correctly handle pytz timezones (which require localize()) and standard tzinfo objects
    tz = run_datetime_ist.tzinfo
    naive_start = datetime.combine(run_date, datetime.min.time()) + timedelta(minutes=30)
    naive_end = datetime.combine(run_date, datetime.min.time()) + timedelta(hours=7)
    
    if hasattr(tz, 'localize'):
        start_boundary = tz.localize(naive_start)
        end_boundary = tz.localize(naive_end)
    else:
        start_boundary = naive_start.replace(tzinfo=tz)
        end_boundary = naive_end.replace(tzinfo=tz)
    
    for event in events:
        utc_time_str = event.get("date")
        if not utc_time_str:
            continue
            
        try:
            if utc_time_str.endswith("Z"):
                utc_time_str = utc_time_str.replace("Z", "+00:00")
            dt_utc = datetime.fromisoformat(utc_time_str)
            dt_ist = dt_utc.astimezone(run_datetime_ist.tzinfo)
        except Exception as e:
            logger.error(f"Error parsing date {utc_time_str}: {e}")
            continue
            
        comps = event.get("competitions", [])
        if not comps:
            continue
        comp = comps[0]
        
        competitors = comp.get("competitors", [])
        if len(competitors) < 2:
            continue
            
        home_team = None
        away_team = None
        for competitor in competitors:
            role = competitor.get("homeAway")
            team_name = competitor.get("team", {}).get("displayName", "Unknown")
            score = competitor.get("score", "0")
            
            if role == "home":
                home_team = {"name": team_name, "score": score}
            elif role == "away":
                away_team = {"name": team_name, "score": score}
                
        if not home_team or not away_team:
            continue
            
        status = event.get("status", {})
        status_type = status.get("type", {})
        state = status_type.get("state", "")
        completed = status_type.get("completed", False)
        
        scorers_str = parse_scorers(comp)
        
        match_info = {
            "home_team": home_team["name"],
            "away_team": away_team["name"],
            "home_score": home_team["score"],
            "away_score": away_team["score"],
            "status_detail": status.get("detail", ""),
            "clock": status.get("displayClock", ""),
            "kickoff_ist": dt_ist.strftime("%I:%M %p"),
            "scorers": scorers_str
        }
        
        # Categorize
        if state == "in":
            subpart_b.append(match_info)
        elif completed or state == "post":
            if start_boundary <= dt_ist <= end_boundary:
                subpart_a.append(match_info)
        elif state == "pre":
            match_date_ist = dt_ist.date()
            if match_date_ist == run_date:
                if dt_ist > end_boundary:
                    subpart_c.append(match_info)
            elif match_date_ist == tomorrow_date:
                subpart_d.append(match_info)
                
    # If no games fell into any category
    if not (subpart_a or subpart_b or subpart_c or subpart_d):
        return {
            "has_data": False,
            "briefing": "No World Cup matches today"
        }
        
    return {
        "has_data": True,
        "subpart_a": subpart_a,
        "subpart_b": subpart_b,
        "subpart_c": subpart_c,
        "subpart_d": subpart_d
    }
