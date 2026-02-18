import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import DashboardEnhanced from './pages/DashboardEnhanced';
import ComprehensiveDashboard from './pages/ComprehensiveDashboard';
import Analytics from './pages/Analytics';
import AdminPanel from './pages/AdminPanel';
import MLFeatures from './pages/MLFeatures';

const Navigation: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '🛡️' },
    { path: '/comprehensive', label: 'Analytics & Graphs', icon: '📈' },
    { path: '/analytics', label: 'Endpoint Analytics', icon: '🎯' },
    { path: '/ml-features', label: 'ML Features', icon: '🤖' },
    { path: '/admin', label: 'Admin Panel', icon: '⚙️' },
  ];

  return (
    <nav className="bg-dark-card border-b border-dark-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-bold text-dark-text">
                🛡️ API Misuse Detection
              </h1>
            </div>
            <div className="ml-10 flex items-baseline space-x-4">
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-primary-500 text-white'
                        : 'text-dark-muted hover:bg-dark-border hover:text-dark-text'
                    }`}
                  >
                    <span className="mr-2">{item.icon}</span>
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-dark-bg">
        <Navigation />
        <main className="max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<DashboardEnhanced />} />
            <Route path="/comprehensive" element={<ComprehensiveDashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/ml-features" element={<MLFeatures />} />
            <Route path="/admin" element={<AdminPanel />} />
          </Routes>
        </main>
        <Toaster
          position="top-right"
          toastOptions={{
            className: '',
            style: {
              background: '#1a1f3a',
              color: '#e5e7eb',
              border: '1px solid #2a2f4a',
            },
          }}
        />
      </div>
    </Router>
  );
};

export default App;
