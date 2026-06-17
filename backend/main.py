from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from database import get_db, engine
import models
import schemas
import services

# Automatically create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="World Cup Tracker API")

# Configure CORS to allow your React app to fetch data securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Backend server is running smoothly"}

@app.get("/db-test")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result[0] == 1:
            return {"database_status": "Connected successfully to world_cup_db!"}
    except Exception as e:
        return {"database_status": "Connection failed", "error": str(e)}

# --- TEAM ROUTES ---

@app.post("/api/teams/", response_model=schemas.TeamResponse)
def create_team(team: schemas.TeamCreate, db: Session = Depends(get_db)):
    # Check if a team with this name or code already exists to prevent duplicates
    existing_team = db.query(models.Team).filter(
        (models.Team.name == team.name) | (models.Team.country_code == team.country_code)
    ).first()
    
    if existing_team:
        raise HTTPException(status_code=400, detail="Team or Country Code already registered")

    db_team = models.Team(**team.model_dump())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

@app.get("/api/teams/", response_model=list[schemas.TeamResponse])
def get_all_teams(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Team).offset(skip).limit(limit).all()

# --- MATCH ROUTES ---

@app.post("/api/matches/", response_model=schemas.MatchResponse)
def create_match(match: schemas.MatchCreate, db: Session = Depends(get_db)):
    # Business Logic: A team cannot play itself
    if match.home_team_id == match.away_team_id:
        raise HTTPException(status_code=400, detail="A team cannot play against itself")

    # Verify both teams actually exist in the database
    home_team = db.query(models.Team).filter(models.Team.team_id == match.home_team_id).first()
    away_team = db.query(models.Team).filter(models.Team.team_id == match.away_team_id).first()
    
    if not home_team or not away_team:
        raise HTTPException(status_code=404, detail="One or both teams not found in the database")

    db_match = models.Match(**match.model_dump())
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match

@app.get("/api/matches/", response_model=list[schemas.MatchResponse])
def get_all_matches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Match).offset(skip).limit(limit).all()

@app.get("/api/matches/today", response_model=list[schemas.MatchResponse])
def get_todays_matches(db: Session = Depends(get_db)):
    """
    Returns only matches scheduled, in-play, or finished for today.
    Perfect for your React app's main dashboard feed.
    """
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # UPDATED: Changed match_date to kickoff_time to match models.py
    return db.query(models.Match).filter(
        models.Match.kickoff_time >= today_start,
        models.Match.kickoff_time <= today_end
    ).all()

# --- PLAYER ROUTES ---

@app.post("/api/players/", response_model=schemas.PlayerResponse)
def create_player(player: schemas.PlayerCreate, db: Session = Depends(get_db)):
    db_player = models.Player(**player.model_dump())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player

# --- MATCH EVENT ROUTES (The Core Tracker Logic) ---

@app.post("/api/events/", response_model=schemas.MatchEventResponse)
def create_match_event(event: schemas.MatchEventCreate, db: Session = Depends(get_db)):
    db_event = models.MatchEvent(**event.model_dump())
    db.add(db_event)
    
    # Automatically update live score if event is a goal
    if event.event_type == models.MatchEventType.goal and event.player_id:
        match = db.query(models.Match).filter(models.Match.match_id == event.match_id).first()
        player = db.query(models.Player).filter(models.Player.player_id == event.player_id).first()
        
        if match and player:
            if player.team_id == match.home_team_id:
                match.home_score += 1
            elif player.team_id == match.away_team_id:
                match.away_score += 1

    db.commit()
    db.refresh(db_event)
    return db_event

@app.get("/api/matches/{match_id}/events", response_model=list[schemas.MatchEventResponse])
def get_match_timeline(match_id: int, db: Session = Depends(get_db)):
    return db.query(models.MatchEvent).filter(
        models.MatchEvent.match_id == match_id
    ).order_by(models.MatchEvent.match_minute.asc()).all()

# --- EXTERNAL SYNC ROUTE ---

@app.post("/api/sync-live-data/")
def sync_with_world_api(db: Session = Depends(get_db)):
    """
    Triggers your live service module to fetch data from API-Football
    and sync live scores into your local PostgreSQL tables.
    """
    result = services.fetch_and_sync_live_matches(db)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

# --- STANDINGS ROUTE ---

@app.get("/api/standings/{group_letter}", response_model=list[schemas.TeamStanding])
def get_group_standings(group_letter: str, db: Session = Depends(get_db)):
    teams = db.query(models.Team).filter(models.Team.group_letter == group_letter.upper()).all()
    standings = []
    
    for team in teams:
        matches = db.query(models.Match).filter(
            ((models.Match.home_team_id == team.team_id) | (models.Match.away_team_id == team.team_id)) &
            (models.Match.status != models.MatchStatus.scheduled)
        ).all()
        
        mp, w, d, l, gf, ga, pts = 0, 0, 0, 0, 0, 0, 0
        
        for match in matches:
            mp += 1
            if match.home_team_id == team.team_id:
                gf += match.home_score
                ga += match.away_score
                if match.home_score > match.away_score:
                    w += 1
                    pts += 3
                elif match.home_score == match.away_score:
                    d += 1
                    pts += 1
                else:
                    l += 1
            else:
                gf += match.away_score
                ga += match.home_score
                if match.away_score > match.home_score:
                    w += 1
                    pts += 3
                elif match.away_score == match.home_score:
                    d += 1
                    pts += 1
                else:
                    l += 1
                    
        standings.append({
            "team_id": team.team_id,
            "name": team.name,
            "country_code": team.country_code,
            "group_letter": team.group_letter,
            "matches_played": mp,
            "wins": w,
            "draws": d,
            "losses": l,
            "goals_for": gf,
            "goals_against": ga,
            "goal_differential": gf - ga,
            "points": pts
        })
        
    sorted_standings = sorted(
        standings, 
        key=lambda x: (x["points"], x["goal_differential"], x["goals_for"]), 
        reverse=True
    )
    
    return sorted_standings

# --- DATABASE RESET ROUTE (DEV ONLY) ---

@app.delete("/api/reset-db/")
def wipe_database(db: Session = Depends(get_db)):
    """
    Wipes all data from the database. 
    Used to clear out 2022 data before syncing 2026 data.
    """
    try:
        # Delete in order of relationships to avoid foreign key errors
        db.query(models.MatchEvent).delete()
        db.query(models.Match).delete()
        db.query(models.Player).delete()
        db.query(models.Team).delete()
        db.commit()
        return {"status": "success", "message": "Database wiped completely clean. Ready for 2026."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))