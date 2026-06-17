import React, { useState, useEffect } from 'react';
import api from '../api';
import { Activity, Calendar } from 'lucide-react';

const LiveMatchFeed = () => {
    const [matches, setMatches] = useState([]);
    const [teams, setTeams] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                // Fetch both tables simultaneously
                const [matchesResponse, teamsResponse] = await Promise.all([
                    api.get('/matches/'), // Fetching ALL matches instead of just today
                    api.get('/teams/')    // Fetching the teams lookup table
                ]);

                // Create a dictionary to easily look up team names by their ID
                // Example: { 1: "Brazil", 2: "France" }
                const teamLookup = {};
                teamsResponse.data.forEach(team => {
                    teamLookup[team.team_id] = team.name;
                });

                setTeams(teamLookup);
                
                // Sort matches chronologically by kickoff time
                const sortedMatches = matchesResponse.data.sort((a, b) => 
                    new Date(a.kickoff_time) - new Date(b.kickoff_time)
                );
                
                setMatches(sortedMatches);
                setLoading(false);
            } catch (error) {
                console.error("Error fetching dashboard data:", error);
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    if (loading) return <div style={{ textAlign: 'center', marginTop: '50px' }}>Loading World Cup Database...</div>;

    return (
        <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Calendar color="#333" size={24} /> Full Tournament Schedule
            </h2>
            
            <p style={{ color: 'gray', marginBottom: '20px' }}>
                Displaying all {matches.length} matches from your PostgreSQL database.
            </p>
            
            {matches.length === 0 ? (
                <p>No matches found in the database. Run the sync script!</p>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                    {matches.map((match) => (
                        <div key={match.match_id} style={{
                            border: '1px solid #e0e0e0',
                            borderRadius: '8px',
                            padding: '15px',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            backgroundColor: 'white',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                        }}>
                            {/* Home Team */}
                            <div style={{ fontSize: '18px', fontWeight: 'bold', flex: 1, textAlign: 'right', color: '#1a1a1a' }}>
                                {teams[match.home_team_id] || `Team ${match.home_team_id}`}
                            </div>
                            
                            {/* Score & Time */}
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '0 20px' }}>
                                <div style={{ fontSize: '24px', fontWeight: '900', color: '#333' }}>
                                    {match.home_score} - {match.away_score}
                                </div>
                                <div style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
                                    {new Date(match.kickoff_time).toLocaleDateString()}
                                </div>
                            </div>
                            
                            {/* Away Team */}
                            <div style={{ fontSize: '18px', fontWeight: 'bold', flex: 1, textAlign: 'left', color: '#1a1a1a' }}>
                                {teams[match.away_team_id] || `Team ${match.away_team_id}`}
                            </div>
                            
                            {/* Match Status */}
                            <div style={{ fontSize: '12px', width: '80px', textAlign: 'right', color: match.status === 'in_play' ? 'red' : 'gray', fontWeight: 'bold' }}>
                                {match.status.toUpperCase().replace('_', ' ')}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default LiveMatchFeed;