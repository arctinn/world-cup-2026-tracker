import requests
from sqlalchemy.orm import Session
import models
from datetime import datetime

def fetch_and_sync_live_matches(db: Session):
    # Pulls the entire LIVE 2026 World Cup tournament (June 11 - July 19)
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates=20260611-20260719"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return {"status": "error", "message": f"ESPN blocked the request: {response.status_code}"}
            
        data = response.json()
        events = data.get("events", [])
        
        if not events:
             return {"status": "success", "message": "ESPN returned 0 matches for this date range."}

        updated_matches = 0
        added_teams = 0

        for event in events:
            date_str = event["date"]
            try:
                match_time = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                match_time = datetime.strptime(date_str, "%Y-%m-%dT%H:%MZ")
            
            competition = event["competitions"][0]
            competitors = competition["competitors"]
            status_state = event["status"]["type"]["state"]

            home_comp = next((c for c in competitors if c["homeAway"] == "home"), None)
            away_comp = next((c for c in competitors if c["homeAway"] == "away"), None)

            if not home_comp or not away_comp:
                continue

            home_name = home_comp["team"].get("name", "Unknown")
            away_name = away_comp["team"].get("name", "Unknown")
            home_abbr = home_comp["team"].get("abbreviation", "UNK")
            away_abbr = away_comp["team"].get("abbreviation", "UNK")
            
            home_score = int(home_comp.get("score", 0) or 0)
            away_score = int(away_comp.get("score", 0) or 0)

            
            # --- 1. COLLISION-PROOF HOME TEAM CREATION ---
            home_team = db.query(models.Team).filter(models.Team.name == home_name).first()
            if not home_team and home_name != "Unknown":
                safe_abbr = home_abbr[:3].upper() if home_abbr else "UNK"
                suffix = 1
                # If ESPN's abbreviation is already taken, invent a unique one (X01, X02...)
                while db.query(models.Team).filter(models.Team.country_code == safe_abbr).first():
                    safe_abbr = f"X{suffix:02d}"
                    suffix += 1
                    
                home_team = models.Team(name=home_name, country_code=safe_abbr, group_letter="-")
                db.add(home_team)
                db.commit()
                db.refresh(home_team)
                added_teams += 1

            # --- 2. COLLISION-PROOF AWAY TEAM CREATION ---
            away_team = db.query(models.Team).filter(models.Team.name == away_name).first()
            if not away_team and away_name != "Unknown":
                safe_abbr = away_abbr[:3].upper() if away_abbr else "UNK"
                suffix = 1
                while db.query(models.Team).filter(models.Team.country_code == safe_abbr).first():
                    safe_abbr = f"X{suffix:02d}"
                    suffix += 1
                    
                away_team = models.Team(name=away_name, country_code=safe_abbr, group_letter="-")
                db.add(away_team)
                db.commit()
                db.refresh(away_team)
                added_teams += 1

            if not home_team or not away_team:
                continue

            # --- 3. AUTO-SEED MATCHES ---
            db_match = db.query(models.Match).filter(
                models.Match.home_team_id == home_team.team_id,
                models.Match.away_team_id == away_team.team_id,
                models.Match.kickoff_time == match_time
            ).first()

            if not db_match:
                db_match = models.Match(
                    home_team_id=home_team.team_id,
                    away_team_id=away_team.team_id,
                    kickoff_time=match_time,
                    status=models.MatchStatus.scheduled
                )
                db.add(db_match)
                db.commit()
                db.refresh(db_match)

            if status_state == "in":
                db_match.status = models.MatchStatus.in_play
            elif status_state == "post":
                db_match.status = models.MatchStatus.finished
            else:
                db_match.status = models.MatchStatus.scheduled

            db_match.home_score = home_score
            db_match.away_score = away_score
            updated_matches += 1

        db.commit()
        return {
            "status": "success", 
            "message": f"ESPN Sync Complete. Seeded {added_teams} new teams and processed {updated_matches} matches."
        }

    except Exception as e:
        db.rollback() 
        return {"status": "error", "message": f"ESPN Parsing Crash: {str(e)}"}