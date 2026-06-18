import { useState, useEffect } from 'react';
import axios from 'axios';

export default function StatsLeaderboard() {
  const [leaders, setLeaders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('http://localhost:8000/api/stats/golden-boot')
      .then(response => {
        setLeaders(response.data);
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching stats:", error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-dash-accent"></div>
      </div>
    );
  }

  return (
    <div className="bg-dash-card border border-slate-700 rounded-xl overflow-hidden shadow-lg max-w-4xl mx-auto">
      <div className="px-6 py-4 border-b border-slate-700 bg-slate-800/50 flex justify-between items-center">
        <h2 className="text-xl font-bold text-white">Golden Boot Race</h2>
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Top 10 Scorers</span>
      </div>
      
      <div className="divide-y divide-slate-700/50">
        {leaders.length === 0 ? (
          <div className="p-6 text-center text-slate-400">No goals recorded yet in the tournament.</div>
        ) : (
          leaders.map((player, index) => (
            <div key={index} className="flex items-center p-4 hover:bg-slate-800/30 transition-colors">
              {/* Rank */}
              <div className="w-8 text-center font-bold text-slate-500">{index + 1}</div>
              
              {/* Player Info */}
              <div className="flex-1 flex items-center ml-4">
                <div className="h-10 w-10 rounded-full bg-slate-700 overflow-hidden flex-shrink-0 border border-slate-600">
                  {player.headshot_url ? (
                    <img src={player.headshot_url} alt={player.name} className="h-full w-full object-cover" />
                  ) : (
                    <div className="h-full w-full flex items-center justify-center text-slate-400 text-xs">No Pic</div>
                  )}
                </div>
                <div className="ml-4">
                  <div className="font-semibold text-white text-lg">{player.name}</div>
                  <div className="flex items-center text-sm text-slate-400 mt-0.5">
                    {player.flag_url && <img src={player.flag_url} alt="flag" className="h-3 mr-2" />}
                    {player.country} • #{player.jersey_number || 'N/A'} {player.position && `• ${player.position}`}
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="flex space-x-6 text-center">
                <div>
                  <div className="text-xs text-slate-500 uppercase">Assists</div>
                  <div className="font-semibold text-slate-300">{player.assists}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 uppercase text-dash-accent">Goals</div>
                  <div className="font-bold text-2xl text-white">{player.goals}</div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}