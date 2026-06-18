import React, { useState, useEffect } from 'react';

const MatchCenter = () => {
  // ==========================================
  // 1. DATA FETCHING STATE
  // ==========================================
  const [matches, setMatches] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadMatches = async () => {
      try {
        // Fetch directly from your FastAPI backend
        const response = await fetch('http://localhost:8000/api/matches');
        if (response.ok) {
          const data = await response.json();
          setMatches(data);
        } else {
          console.error("Backend returned an error:", response.status);
        }
      } catch (error) {
        console.error("Failed to connect to Match API:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadMatches();
  }, []);

  // ==========================================
  // 2. TIME & DATE LOGIC
  // ==========================================
  const today = new Date();
  
  const isToday = (dateString) => {
    const date = new Date(dateString);
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
  };

  const formatMatchTime = (dateString) => {
    const options = { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString('en-US', options);
  };

  // ==========================================
  // 3. DATA BUCKETING
  // ==========================================
  const liveMatches = matches.filter(m => m.status === 'in');
  
  const todayMatches = matches.filter(m => m.status === 'pre' && isToday(m.match_time))
                             .sort((a, b) => new Date(a.match_time) - new Date(b.match_time));
                               
  // Captures all finished games, sorting the most recently finished to the top
  const recentMatches = matches.filter(m => m.status === 'post')
                               .sort((a, b) => new Date(b.match_time) - new Date(a.match_time));
                               
  const upcomingMatches = matches.filter(m => m.status === 'pre' && !isToday(m.match_time))
                                 .sort((a, b) => new Date(a.match_time) - new Date(b.match_time));

  // ==========================================
  // 4. MODERN CARD COMPONENT
  // ==========================================
  const MatchCard = ({ match, type }) => {
    const isLive = type === 'live';
    const isFinal = type === 'recent';

    return (
      <div className={`relative p-5 rounded-xl border backdrop-blur-md transition-all duration-300 hover:-translate-y-1 cursor-default
        ${isLive 
          ? 'bg-slate-800/80 border-red-500/50 shadow-[0_0_20px_rgba(239,68,68,0.2)]' 
          : 'bg-slate-800/40 border-slate-700/50 hover:bg-slate-800/60 hover:shadow-lg hover:shadow-cyan-900/20 hover:border-slate-600/50'
        }`}
      >
        {/* Card Header */}
        <div className="flex justify-between items-center mb-5 border-b border-slate-700/50 pb-3">
          <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
            {formatMatchTime(match.match_time)}
          </span>
          
          {isLive && (
            <span className="flex items-center gap-2 px-2.5 py-1 bg-red-500/10 text-red-500 text-[10px] font-black tracking-widest rounded ring-1 ring-red-500/50 shadow-[0_0_10px_rgba(239,68,68,0.4)]">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
              LIVE
            </span>
          )}
          {isFinal && (
            <span className="px-2 py-1 bg-slate-700/50 text-slate-300 text-[10px] font-bold tracking-widest rounded">
              FINAL
            </span>
          )}
          {!isLive && !isFinal && (
            <span className="px-2 py-1 bg-cyan-900/30 text-cyan-400 text-[10px] font-bold tracking-widest rounded ring-1 ring-cyan-500/30">
              UPCOMING
            </span>
          )}
        </div>

        {/* Card Body */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className={`font-bold text-lg tracking-wide ${isLive ? 'text-white' : 'text-slate-200'}`}>
              {match.home_team}
            </span>
            <span className={`text-2xl font-black ${isLive ? 'text-red-400' : isFinal ? 'text-white' : 'text-slate-600'}`}>
              {isFinal || isLive ? match.home_score : '-'}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <span className={`font-bold text-lg tracking-wide ${isLive ? 'text-white' : 'text-slate-200'}`}>
              {match.away_team}
            </span>
            <span className={`text-2xl font-black ${isLive ? 'text-red-400' : isFinal ? 'text-white' : 'text-slate-600'}`}>
              {isFinal || isLive ? match.away_score : '-'}
            </span>
          </div>
        </div>
      </div>
    );
  };

  // ==========================================
  // 5. MAIN LAYOUT RENDER
  // ==========================================
  if (isLoading) {
    return (
      <div className="w-full py-20 flex flex-col items-center justify-center text-slate-500">
        <div className="w-16 h-16 border-4 border-slate-700 border-t-cyan-500 rounded-full animate-spin mb-4"></div>
        <p className="font-semibold tracking-widest uppercase">Loading Match Data Pipeline...</p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-12 pb-10">
      
      {/* SECTION 1: LIVE NOW */}
      {liveMatches.length > 0 && (
        <section>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-2 h-6 bg-red-500 rounded-sm animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.6)]"></div>
            <h2 className="text-xl font-black text-white uppercase tracking-wider">Live Now</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {liveMatches.map(match => <MatchCard key={match.id} match={match} type="live" />)}
          </div>
        </section>
      )}

      {/* SECTION 2: TODAY'S MATCHES */}
      {todayMatches.length > 0 && (
        <section>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-2 h-6 bg-cyan-500 rounded-sm shadow-[0_0_10px_rgba(6,182,212,0.4)]"></div>
            <h2 className="text-xl font-black text-white uppercase tracking-wider">Today's Matches</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {todayMatches.map(match => <MatchCard key={match.id} match={match} type="today" />)}
          </div>
        </section>
      )}

      {/* SECTION 3: RECENT RESULTS */}
      {recentMatches.length > 0 && (
        <section>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-2 h-6 bg-slate-500 rounded-sm"></div>
            <h2 className="text-xl font-black text-slate-200 uppercase tracking-wider">Recent Results</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {recentMatches.slice(0, 6).map(match => <MatchCard key={match.id} match={match} type="recent" />)}
          </div>
        </section>
      )}

      {/* SECTION 4: UPCOMING SCHEDULE */}
      {upcomingMatches.length > 0 && (
        <section>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-2 h-6 bg-slate-700 rounded-sm"></div>
            <h2 className="text-xl font-black text-slate-400 uppercase tracking-wider">Upcoming Schedule</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {upcomingMatches.slice(0, 9).map(match => <MatchCard key={match.id} match={match} type="upcoming" />)}
          </div>
        </section>
      )}

      {/* EMPTY STATE FALLBACK (If DB is empty) */}
      {!isLoading && matches.length === 0 && (
        <div className="w-full py-20 flex flex-col items-center justify-center text-slate-500">
          <p className="font-semibold tracking-widest uppercase">No matches found. Please sync the database.</p>
        </div>
      )}

    </div>
  );
};

export default MatchCenter;