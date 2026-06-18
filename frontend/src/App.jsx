import { useState } from 'react';
import MatchCenter from './components/MatchCenter';
import StandingsGrid from './components/StandingsGrid';
import StatsLeaderboard from './components/StatsLeaderboard';

function App() {
  // State to track which tab the user is currently viewing
  const [activeTab, setActiveTab] = useState('matches');

  return (
    <div className="min-h-screen font-sans bg-[#0f172a] text-white">
      
      {/* Jumbotron / Header */}
      <header className="bg-dash-card border-b border-slate-700 py-6 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">
              2026 World Cup <span className="text-dash-accent">Tracker</span>
            </h1>
            <p className="text-slate-400 text-sm mt-1">Live Match Data & Group Standings</p>
          </div>
          <div className="hidden sm:block">
             <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-xs font-semibold border border-green-500/30">
                Data Pipeline: ONLINE
             </span>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <nav className="flex space-x-4 border-b border-slate-700 pb-px">
          <button 
            onClick={() => setActiveTab('matches')}
            className={`py-2 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'matches' 
                ? 'border-dash-accent text-dash-accent' 
                : 'border-transparent text-slate-400 hover:text-white hover:border-slate-500'
            }`}
          >
            Live & Upcoming Matches
          </button>
          
          <button 
            onClick={() => setActiveTab('standings')}
            className={`py-2 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'standings' 
                ? 'border-dash-accent text-dash-accent' 
                : 'border-transparent text-slate-400 hover:text-white hover:border-slate-500'
            }`}
          >
            Group Standings
          </button>

          <button 
            onClick={() => setActiveTab('stats')}
            className={`py-2 px-4 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'stats' 
                ? 'border-dash-accent text-dash-accent' 
                : 'border-transparent text-slate-400 hover:text-white hover:border-slate-500'
            }`}
          >
            Golden Boot Race
          </button>
        </nav>
      </div>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {activeTab === 'matches' && (
          <div className="animate-fade-in">
             <MatchCenter />
          </div>
        )}
        
        {activeTab === 'standings' && (
          <div className="animate-fade-in">
             <StandingsGrid />
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="animate-fade-in">
             <StatsLeaderboard />
          </div>
        )}
        
      </main>

    </div>
  );
}

export default App;