from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_score = Column(Integer, default=0)  
    away_score = Column(Integer, default=0)  
    status = Column(String, nullable=False)
    match_time = Column(DateTime, nullable=False)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    espn_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    abbreviation = Column(String, nullable=False)
    logo_url = Column(String, nullable=True)
    
    # Relationships
    standings = relationship("Standing", back_populates="team", cascade="all, delete-orphan")
    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")


class Standing(Base):
    __tablename__ = "standings"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    group_name = Column(String, nullable=False)
    points = Column(Integer, default=0)
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    goal_differential = Column(Integer, default=0)
    
    team = relationship("Team", back_populates="standings")


class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    espn_id = Column(String, unique=True, index=True, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    position = Column(String, nullable=True)
    jersey_number = Column(String, nullable=True)
    headshot_url = Column(String, nullable=True)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    
    team = relationship("Team", back_populates="players")