import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class StageType(enum.Enum):
    group_stage = 'group_stage'
    round_of_32 = 'round_of_32'
    round_of_16 = 'round_of_16'
    quarter_final = 'quarter_final'
    semi_final = 'semi_final'
    third_place = 'third_place'
    final = 'final'

class MatchStatus(enum.Enum):
    scheduled = 'scheduled'
    in_play = 'in_play'
    paused = 'paused'
    finished = 'finished'
    postponed = 'postponed'

class PlayerPosition(enum.Enum):
    GK = 'GK'
    DF = 'DF'
    MF = 'MF'
    FW = 'FW'

class MatchEventType(enum.Enum):
    goal = 'goal'
    own_goal = 'own_goal'
    penalty = 'penalty'
    yellow_card = 'yellow_card'
    red_card = 'red_card'
    substitution = 'substitution'
    var_review = 'var_review'

class Team(Base):
    __tablename__ = "teams"
    
    team_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    country_code = Column(String(3), unique=True, nullable=False)
    group_letter = Column(String(1), nullable=False)
    flag_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")

class Player(Base):
    __tablename__ = "players"

    player_id = Column(Integer, primary_key=True, index=True) # Maps perfectly to Sportmonks Player ID
    team_id = Column(Integer, ForeignKey("teams.team_id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False, index=True)
    jersey_number = Column(Integer, nullable=True)
    position = Column(SQLEnum(PlayerPosition), nullable=True)
    is_captain = Column(Boolean, default=False)
    
    # Unified Sportmonks metadata
    domestic_club_name = Column(String(100), nullable=True)

    team = relationship("Team", back_populates="players")
    events = relationship("MatchEvent", foreign_keys="[MatchEvent.player_id]", back_populates="player")

class Match(Base):
    __tablename__ = "matches"

    match_id = Column(Integer, primary_key=True, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.team_id"))
    away_team_id = Column(Integer, ForeignKey("teams.team_id"))
    stage = Column(SQLEnum(StageType), nullable=False, default=StageType.group_stage)
    status = Column(SQLEnum(MatchStatus), nullable=False, default=MatchStatus.scheduled)
    home_score = Column(Integer, default=0)
    away_score = Column(Integer, default=0)
    stadium = Column(String(100))
    kickoff_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    events = relationship("MatchEvent", back_populates="match", cascade="all, delete-orphan")

class MatchEvent(Base):
    __tablename__ = "match_events"

    event_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.match_id", ondelete="CASCADE"))
    event_type = Column(SQLEnum(MatchEventType), nullable=False)
    match_minute = Column(Integer, nullable=False)
    stoppage_minute = Column(Integer, default=0)
    
    # Relational links to our unified Player table
    player_id = Column(Integer, ForeignKey("players.player_id", ondelete="SET NULL"), nullable=True)
    detail_player_id = Column(Integer, ForeignKey("players.player_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    match = relationship("Match", back_populates="events")
    player = relationship("Player", foreign_keys=[player_id], back_populates="events")