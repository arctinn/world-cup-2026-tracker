import requests
from datetime import datetime
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import func
from playwright.sync_api import sync_playwright 
import models

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
}

# ==========================================
# 1. DYNAMIC TEAMS
# ==========================================
def fetch_and_sync_teams(db: Session):
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/teams"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        teams_data = data.get("sports", [])[0].get("leagues", [])[0].get("teams", [])
        
        for item in teams_data:
            team = item.get("team", {})
            espn_id = str(team.get("id"))
            
            existing_team = db.query(models.Team).filter(models.Team.espn_id == espn_id).first()
            if not existing_team:
                new_team = models.Team(
                    espn_id=espn_id, name=team.get("name"), 
                    abbreviation=team.get("abbreviation"), logo_url=team.get("logos", [{}])[0].get("href")
                )
                db.add(new_team)
            else:
                existing_team.name = team.get("name")
                existing_team.abbreviation = team.get("abbreviation")
                existing_team.logo_url = team.get("logos", [{}])[0].get("href")
                
        db.commit()
        return {"status": "success", "message": "Teams dynamically synced."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# 2. DYNAMIC STANDINGS (Fixed Core Endpoint)
# ==========================================
def fetch_and_sync_standings(db: Session):
    # CRITICAL FIX: Changed /apis/site/v2/ to /apis/v2/ to access the real group mappings
    url = "https://site.api.espn.com/apis/v2/sports/soccer/fifa.world/standings"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        
        db.query(models.Standing).delete()
        
        for group in data.get("children", []):
            group_name = group.get("name", "Unknown Group") 
            
            for entry in group.get("standings", {}).get("entries", []):
                espn_team_id = str(entry.get("team", {}).get("id"))
                team = db.query(models.Team).filter(models.Team.espn_id == espn_team_id).first()
                
                if not team:
                    continue
                    
                stats = {s.get("name"): s.get("value", 0) for s in entry.get("stats", []) if s.get("name")}
                
                new_standing = models.Standing(
                    team_id=team.id, 
                    group_name=group_name,
                    points=stats.get("points", 0), 
                    matches_played=stats.get("gamesPlayed", 0),
                    wins=stats.get("wins", 0), 
                    draws=stats.get("ties", 0), 
                    losses=stats.get("losses", 0),
                    goals_for=stats.get("pointsFor", 0), 
                    goals_against=stats.get("pointsAgainst", 0),
                    goal_differential=stats.get("pointDifferential", 0)
                )
                db.add(new_standing)
                
        db.commit()
        return {"status": "success", "message": "Standings successfully mapped from API."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# 3. DYNAMIC MATCH HISTORY & SCHEDULE
# ==========================================
def fetch_and_sync_live_matches(db: Session):
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260611-20260719"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        events = response.json().get("events", [])
        
        for event in events:
            match_id = int(event.get("id"))
            status = event.get("status", {}).get("type", {}).get("state", "pre")
            
            match_time_raw = event.get("date", "")
            match_time = datetime.fromisoformat(match_time_raw.replace("Z", "+00:00")) if match_time_raw else datetime.utcnow()
                
            competitors = event.get("competitions", [])[0].get("competitors", [])
            home_team, away_team = "Unknown", "Unknown"
            home_score, away_score = 0, 0
            
            for comp in competitors:
                if comp.get("homeAway") == "home":
                    home_team = comp.get("team", {}).get("name", "Unknown")
                    home_score = int(comp.get("score", 0)) if comp.get("score") else 0
                else:
                    away_team = comp.get("team", {}).get("name", "Unknown")
                    away_score = int(comp.get("score", 0)) if comp.get("score") else 0
                    
            existing_match = db.query(models.Match).filter(models.Match.id == match_id).first()
            
            if not existing_match:
                new_match = models.Match(
                    id=match_id, home_team=home_team, away_team=away_team,
                    home_score=home_score, away_score=away_score, status=status, match_time=match_time
                )
                db.add(new_match)
            else:
                existing_match.home_score = home_score
                existing_match.away_score = away_score
                existing_match.status = status
                existing_match.match_time = match_time
                
        db.commit()
        return {"status": "success", "message": "Full match timeline synced."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# 4. FETCH & SYNC ROSTERS
# ==========================================
def fetch_and_sync_rosters_and_stats(db: Session):
    teams = db.query(models.Team).all()
    if not teams:
        return {"status": "error", "message": "No teams found. Run teams sync first."}
        
    players_added, players_updated = 0, 0
    
    for team in teams:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/teams/{team.espn_id}/roster"
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/teams/{team.espn_id}/roster"
            response = requests.get(url, headers=HEADERS, timeout=10)
            
        if response.status_code != 200:
            continue
            
        data = response.json()
        athletes_raw = data.get("athletes", [])
        
        player_list = []
        if athletes_raw and "items" in athletes_raw[0]:
            for group in athletes_raw:
                player_list.extend(group.get("items", []))
        else:
            player_list = athletes_raw
            
        for item in player_list:
            player_espn_id = str(item.get("id", ""))
            if not player_espn_id:
                continue
                
            display_name = item.get("displayName", "Unknown")
            jersey = item.get("jersey", "")
            position_name = item.get("position", {}).get("name", "Unknown")
            headshot = item.get("headshot", {}).get("href", None)
            
            existing_player = db.query(models.Player).filter(models.Player.espn_id == player_espn_id).first()
            
            if not existing_player:
                new_player = models.Player(
                    espn_id=player_espn_id, team_id=team.id, name=display_name,
                    position=position_name, jersey_number=str(jersey), headshot_url=headshot,
                    goals=0, assists=0
                )
                db.add(new_player)
                players_added += 1
            else:
                existing_player.name = display_name
                existing_player.position = position_name
                existing_player.jersey_number = str(jersey)
                existing_player.headshot_url = headshot
                players_updated += 1
                
    db.commit()
    return {"status": "success", "message": f"Rosters synced: {players_added} added, {players_updated} updated."}

# ==========================================
# 5. DYNAMIC GOLDEN BOOT (PRODUCTION OPTIMIZED)
# ==========================================
def fetch_and_sync_leaders(db: Session):
    """
    Dynamically extracts live tournament top scorers from Transfermarkt using an automated
    headless browser pipeline. Resolves all structural database constraints and normalizes
    player images to high-resolution asset formats on the fly.
    """
    url = "https://www.transfermarkt.com/weltmeisterschaft/torschuetzenliste/pokalwettbewerb/FIWC/saison_id/2025"
    
    try:
        html_content = ""
        
        # 1. Initialize Headless Browser Context
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=HEADERS["User-Agent"],
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()
            
            # Navigate to the target metrics page and ensure DOM structural elements are ready
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_selector("table.items", timeout=15000)
            
            html_content = page.content()
            browser.close()

        # 2. Initialize DOM Parser Tree
        soup = BeautifulSoup(html_content, "html.parser")
        stats_table = soup.find("table", class_="items")
        if not stats_table:
            return {"status": "error", "message": "Pipeline halted: Transfermarkt's primary stats data structure could not be verified in the DOM."}
        
        tbody = stats_table.find("tbody")
        if not tbody:
            return {"status": "error", "message": "Pipeline halted: Table structure is missing data rows."}
        
        # Clear out historical goals counts before updating to maintain real-time accuracy
        db.query(models.Player).update({"goals": 0})
        
        updated_count = 0
        added_count = 0

        # 3. Process Table Rows Individually
        for row in tbody.find_all("tr", recursive=False):
            name_cell = row.select_one("td.hauptlink a")
            if not name_cell: 
                continue
            
            player_name = name_cell.text.strip()
            
            # Isolate numerical scoring metrics out of the table's trailing aligned columns
            zentriert_cells = row.find_all("td", class_="zentriert")
            if not zentriert_cells:
                continue
                
            try:
                goals = int(zentriert_cells[-1].text.strip() or 0)
            except (ValueError, IndexError):
                goals = 0
            
            # Intercept and upgrade asset CDN layout structures from small avatars to high-res headers
            img_tag = row.select_one("img.bilderrahmen-fixed") or row.select_one("img.bilderrahmen")
            headshot_url = None
            if img_tag:
                raw_img_url = img_tag.get("data-src") or img_tag.get("src")
                if raw_img_url and "default" not in raw_img_url:
                    headshot_url = raw_img_url.replace("/small/", "/header/").replace("/medium/", "/header/")

            if goals > 0:
                # 4. Perform Strict Case-Insensitive Database Lookups
                player = db.query(models.Player).filter(
                    func.lower(models.Player.name) == player_name.lower()
                ).first()
                
                # Fallback to a precise search check using the surname if naming variations occur across providers
                if not player:
                    surname = player_name.split()[-1].lower()
                    player = db.query(models.Player).filter(
                        func.lower(models.Player.name).contains(surname)
                    ).first()
                
                if player:
                    player.goals = goals
                    if headshot_url:
                        player.headshot_url = headshot_url
                    updated_count += 1
                else:
                    # 5. Team-Aware Entity Isolation (Guarantees Foreign Key Not-Null Constraints)
                    team_cell = row.select_one("td.zentriert img.tiny_logo")
                    team_name = team_cell.get("alt") if team_cell else None
                    
                    if team_name:
                        team = db.query(models.Team).filter(
                            func.lower(models.Team.name).contains(team_name.lower())
                        ).first()
                        
                        # Only insert new entity if relationship integrity can be strictly enforced
                        if team:
                            new_player = models.Player(
                                espn_id=f"tm_{player_name.replace(' ', '')}",
                                team_id=team.id,
                                name=player_name,
                                goals=goals,
                                assists=0,
                                headshot_url=headshot_url
                            )
                            db.add(new_player)
                            added_count += 1

        db.commit()
        return {
            "status": "success", 
            "message": f"Data processing pipeline complete. Updated {updated_count} players, added {added_count} new entries to database tables."
        }

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Pipeline transaction aborted due to execution fault: {str(e)}"}