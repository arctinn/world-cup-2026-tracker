from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import your local files
import models
import services
from database import engine, SessionLocal

# 1. Initialize the FastAPI App ONCE
app = FastAPI(title="World Cup 2026 Data Engine API")

# 2. Add CORS Middleware ONCE so React can communicate securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows any local port (like 5173) to fetch data
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Database Initialization
# NOTE: The DROP TABLE lines are commented out so we don't erase your real data on restart!
# If you ever need to completely nuke the database again, just uncomment these.
# with engine.connect() as conn:
#     conn.execute(text("DROP TABLE IF EXISTS match_events CASCADE"))
#     conn.execute(text("DROP TABLE IF EXISTS players CASCADE"))
#     conn.execute(text("DROP TABLE IF EXISTS standings CASCADE"))
#     conn.execute(text("DROP TABLE IF EXISTS teams CASCADE"))
#     conn.execute(text("DROP TABLE IF EXISTS matches CASCADE"))
#     conn.commit()

# Ensure tables exist
models.Base.metadata.create_all(bind=engine)

# 4. Dependency to get the Database Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Prevent the 404 error when visiting the root URL
@app.get("/")
def read_root():
    return {"message": "World Cup Data Engine is live and running!"}


# =====================================================================
# DATA PIPELINE DATA SYNCHRONIZATION ENDPOINTS (POST)
# =====================================================================

@app.post("/api/sync/matches")
def sync_matches(db: Session = Depends(get_db)):
    result = services.fetch_and_sync_live_matches(db)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.post("/api/sync/teams")
def sync_teams(db: Session = Depends(get_db)):
    result = services.fetch_and_sync_teams(db)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.post("/api/sync/standings")
def sync_standings(db: Session = Depends(get_db)):
    result = services.fetch_and_sync_standings(db)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.post("/api/sync/rosters")
def sync_rosters(db: Session = Depends(get_db)):
    result = services.fetch_and_sync_rosters_and_stats(db)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


# =====================================================================
# FRONTEND API CORE DATA ENDPOINTS (GET)
# =====================================================================

@app.get("/api/matches")
def get_matches(db: Session = Depends(get_db)):
    matches = db.query(models.Match).order_by(models.Match.match_time.asc()).all()
    return matches

@app.get("/api/teams")
def get_teams(db: Session = Depends(get_db)):
    teams = db.query(models.Team).order_by(models.Team.name.asc()).all()
    return teams

@app.get("/api/standings")
def get_standings(db: Session = Depends(get_db)):
    """
    Reads the dynamically synced Group Standings directly from the database.
    """
    standings = db.query(models.Standing).all()
    grouped_standings = {}
    
    for entry in standings:
        team_info = db.query(models.Team).filter(models.Team.id == entry.team_id).first()
        
        entry_data = {
            "team_name": team_info.name if team_info else "Unknown",
            "abbreviation": team_info.abbreviation if team_info else "UNK",
            "logo_url": team_info.logo_url if team_info else None,
            "points": entry.points,
            "matches_played": entry.matches_played,
            "wins": entry.wins,
            "draws": entry.draws,
            "losses": entry.losses,
            "goals_for": entry.goals_for,
            "goals_against": entry.goals_against,
            "goal_differential": entry.goal_differential
        }
        
        if entry.group_name not in grouped_standings:
            grouped_standings[entry.group_name] = []
        grouped_standings[entry.group_name].append(entry_data)
        
    for group in grouped_standings:
        grouped_standings[group].sort(key=lambda x: (x["points"], x["goal_differential"]), reverse=True)
        
    return grouped_standings

@app.get("/api/stats/golden-boot")
def get_golden_boot_leaders(db: Session = Depends(get_db)):
    # Pulls top 10 players sorted by goals, then assists
    leaders = db.query(models.Player)\
                .filter(models.Player.goals > 0)\
                .order_by(models.Player.goals.desc(), models.Player.assists.desc())\
                .limit(10)\
                .all()
    
    output = []
    for player in leaders:
        # Include team details for country flag and name in UI
        team_info = db.query(models.Team).filter(models.Team.id == player.team_id).first()
        output.append({
            "name": player.name,
            "position": player.position,
            "jersey_number": player.jersey_number,
            "headshot_url": player.headshot_url,
            "goals": player.goals,
            "assists": player.assists,
            "country": team_info.name if team_info else "Unknown",
            "flag_url": team_info.logo_url if team_info else None
        })
    return output

import random

@app.post("/api/debug/seed-stats")
def seed_tournament_stats(db: Session = Depends(get_db)):
    # Find all players listed as Attackers/Forwards
    forwards = db.query(models.Player).filter(
        models.Player.position.ilike("%Forward%"),
        models.Player.headshot_url != None # Only pick players with profile pictures for a better UI
    ).limit(30).all()
    
    if not forwards:
        return {"status": "error", "message": "No forwards found. Sync rosters first."}
        
    # Give them realistic tournament stats
    for player in forwards:
        player.goals = random.randint(1, 6)
        player.assists = random.randint(0, 3)
        
    db.commit()
    return {"status": "success", "message": "Golden Boot leaderboard successfully populated with simulated data!"}

@app.post("/api/sync/leaders")
def sync_leaders(db: Session = Depends(get_db)):
    result = services.fetch_and_sync_leaders(db)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.post("/api/debug/reset-db")
def reset_database():
    """
    WARNING: This completely wipes the database and rebuilds it from scratch
    using the latest columns in models.py.
    """
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS players CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS standings CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS matches CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS teams CASCADE"))
        conn.commit()
    
    # Rebuild the fresh tables with the new home_score and away_score columns
    models.Base.metadata.create_all(bind=engine)
    
    return {
        "status": "success", 
        "message": "Database completely wiped and rebuilt with the latest schema. Ready for a fresh sync."
    }