from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from models import StageType, MatchStatus, PlayerPosition, MatchEventType

# --- TEAM SCHEMAS ---
class TeamBase(BaseModel):
    name: str
    country_code: str
    group_letter: str
    flag_url: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamResponse(TeamBase):
    team_id: int

    class Config:
        from_attributes = True

# --- PLAYER SCHEMAS ---
class PlayerBase(BaseModel):
    name: str
    jersey_number: Optional[int] = None
    position: Optional[PlayerPosition] = None
    is_captain: bool = False
    domestic_club_name: Optional[str] = None

class PlayerCreate(PlayerBase):
    team_id: Optional[int] = None

class PlayerResponse(PlayerBase):
    player_id: int
    team_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- MATCH SCHEMAS ---
class MatchBase(BaseModel):
    home_team_id: int
    away_team_id: int
    stage: StageType = StageType.group_stage
    status: MatchStatus = MatchStatus.scheduled
    stadium: Optional[str] = None
    kickoff_time: datetime

class MatchCreate(MatchBase):
    pass

class MatchResponse(MatchBase):
    match_id: int
    home_score: int
    away_score: int

    class Config:
        from_attributes = True

# --- MATCH EVENT SCHEMAS ---
class MatchEventBase(BaseModel):
    event_type: MatchEventType
    match_minute: int
    stoppage_minute: int = 0
    player_id: Optional[int] = None
    detail_player_id: Optional[int] = None

class MatchEventCreate(MatchEventBase):
    match_id: int

class MatchEventResponse(MatchEventBase):
    event_id: int
    match_id: int
    player: Optional[PlayerResponse] = None # Nesting the unified player data structure

    class Config:
        from_attributes = True

# --- ANALYTICS & STANDINGS SCHEMAS ---
class TeamStanding(BaseModel):
    team_id: int
    name: str
    country_code: str
    group_letter: str
    matches_played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_differential: int
    points: int

    class Config:
        from_attributes = True