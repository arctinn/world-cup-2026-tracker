-- Clean up any existing half-baked tables from the previous run
DROP TABLE IF EXISTS match_events CASCADE;
DROP TABLE IF EXISTS matches CASCADE;
DROP TABLE IF EXISTS players CASCADE;
DROP TABLE IF EXISTS teams CASCADE;

-- Clean up any existing custom types
DROP TYPE IF EXISTS stage_type CASCADE;
DROP TYPE IF EXISTS match_status CASCADE;
DROP TYPE IF EXISTS player_position CASCADE;
DROP TYPE IF EXISTS match_event_type CASCADE;

-- 1. Create Custom Types (Fixed the missing comma)
CREATE TYPE stage_type AS ENUM ('group_stage', 'round_of_32', 'round_of_16', 'quarter_final', 'semi_final', 'third_place', 'final');
CREATE TYPE match_status AS ENUM ('scheduled', 'in_play', 'paused', 'finished', 'postponed');
CREATE TYPE player_position AS ENUM ('GK', 'DF', 'MF', 'FW');
CREATE TYPE match_event_type AS ENUM ('goal', 'own_goal', 'penalty', 'yellow_card', 'red_card', 'substitution', 'var_review');

-- 2. Create Tables
CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    country_code VARCHAR(3) UNIQUE NOT NULL,
    group_letter CHAR(1) NOT NULL,
    flag_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    team_id INT REFERENCES teams(team_id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    jersey_number INT NOT NULL,
    position player_position NOT NULL,
    is_captain BOOLEAN DEFAULT FALSE,
    CONSTRAINT unique_team_jersey UNIQUE (team_id, jersey_number)
);

CREATE TABLE matches (
    match_id SERIAL PRIMARY KEY,
    home_team_id INT REFERENCES teams(team_id),
    away_team_id INT REFERENCES teams(team_id),
    stage stage_type NOT NULL DEFAULT 'group_stage',
    status match_status NOT NULL DEFAULT 'scheduled',
    home_score INT DEFAULT 0 CHECK (home_score >= 0),
    away_score INT DEFAULT 0 CHECK (away_score >= 0),
    stadium VARCHAR(100),
    kickoff_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT teams_must_be_different CHECK (home_team_id <> away_team_id)
);

CREATE TABLE match_events (
    event_id SERIAL PRIMARY KEY,
    match_id INT REFERENCES matches(match_id) ON DELETE CASCADE,
    event_type match_event_type NOT NULL,
    match_minute INT NOT NULL CHECK (match_minute BETWEEN 1 AND 120),
    stoppage_minute INT DEFAULT 0 CHECK (stoppage_minute >= 0),
    player_id INT REFERENCES players(player_id), 
    detail_player_id INT REFERENCES players(player_id), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create Optimization Indexes
CREATE INDEX idx_match_events_match_id ON match_events(match_id);
CREATE INDEX idx_matches_status_kickoff ON matches(status, kickoff_time);