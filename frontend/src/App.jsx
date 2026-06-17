import React from 'react';
import LiveMatchFeed from './components/LiveMatchFeed';

function App() {
  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', backgroundColor: '#f4f4f9', minHeight: '100vh', padding: '20px' }}>
      <h1 style={{ textAlign: 'center' }}>🏆 2026 World Cup Tracker</h1>
      <LiveMatchFeed />
    </div>
  );
}

export default App;