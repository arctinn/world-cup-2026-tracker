import { useState, useEffect } from 'react';
import axios from 'axios';

export default function StandingsGrid() {
  const [standings, setStandings] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('http://localhost:8000/api/standings')
      .then(response => {
        setStandings(response.data);
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching standings:", error);
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
    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      {Object.entries(standings).map(([groupName, teams]) => (
        <div key={groupName} className="bg-dash-card border border-slate-700 rounded-xl overflow-hidden shadow-sm">
          <div className="bg-slate-800/80 px-4 py-3 border-b border-slate-700">
            <h3 className="font-bold text-white tracking-wide">{groupName}</h3>
          </div>
          
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-400 bg-slate-800/30 uppercase border-b border-slate-700/50">
              <tr>
                <th className="px-4 py-2 font-medium">Team</th>
                <th className="px-2 py-2 text-center font-medium">MP</th>
                <th className="px-2 py-2 text-center font-medium">GD</th>
                <th className="px-4 py-2 text-center font-bold text-white">Pts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {teams.map((team, index) => (
                <tr key={team.abbreviation} className={index < 2 ? "bg-green-900/10" : ""}>
                  <td className="px-4 py-3 font-medium text-white flex items-center">
                    <span className="w-4 text-slate-500 mr-2 text-xs">{index + 1}</span>
                    {team.logo_url && <img src={team.logo_url} alt="flag" className="h-4 w-6 object-cover mr-3 border border-slate-600 rounded-sm" />}
                    {team.abbreviation}
                  </td>
                  <td className="px-2 py-3 text-center text-slate-300">{team.matches_played}</td>
                  <td className="px-2 py-3 text-center text-slate-300">{team.goal_differential > 0 ? `+${team.goal_differential}` : team.goal_differential}</td>
                  <td className="px-4 py-3 text-center font-bold text-dash-accent">{team.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}