import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { ToastProvider } from './context/ToastContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { MarketTicker } from './components/MarketTicker';

// Pages
import { Dashboard } from './pages/Dashboard';
import { Market } from './pages/Market';
import { StockDetail } from './pages/StockDetail';
import { Watchlists } from './pages/Watchlists';
import { Scanner } from './pages/Scanner';
import { Alerts } from './pages/Alerts';
import { AIAssistant } from './pages/AIAssistant';
import { AINewspaper } from './pages/AINewspaper';
import { Strategies } from './pages/Strategies';
import { Backtests } from './pages/Backtests';
import { Portfolio } from './pages/Portfolio';
import { Wallet } from './pages/Wallet';
import { Settings } from './pages/Settings';
import { Login } from './pages/Login';
import { Register } from './pages/Register';

const ProtectedLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content">
        <MarketTicker />
        <Navbar />
        <main className="content-body">
          {children}
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <WebSocketProvider>
            <Routes>
              {/* Public Auth Routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Protected Platform Routes */}
              <Route path="/dashboard" element={<ProtectedLayout><Dashboard /></ProtectedLayout>} />
              <Route path="/market" element={<ProtectedLayout><Market /></ProtectedLayout>} />
              <Route path="/stock/:symbol" element={<ProtectedLayout><StockDetail /></ProtectedLayout>} />
              <Route path="/watchlists" element={<ProtectedLayout><Watchlists /></ProtectedLayout>} />
              <Route path="/scanner" element={<ProtectedLayout><Scanner /></ProtectedLayout>} />
              <Route path="/alerts" element={<ProtectedLayout><Alerts /></ProtectedLayout>} />
              <Route path="/ai" element={<ProtectedLayout><AIAssistant /></ProtectedLayout>} />
              <Route path="/ai/newspaper" element={<ProtectedLayout><AINewspaper /></ProtectedLayout>} />
              <Route path="/strategies" element={<ProtectedLayout><Strategies /></ProtectedLayout>} />
              <Route path="/backtests" element={<ProtectedLayout><Backtests /></ProtectedLayout>} />
              <Route path="/portfolio" element={<ProtectedLayout><Portfolio /></ProtectedLayout>} />
              <Route path="/wallet" element={<ProtectedLayout><Wallet /></ProtectedLayout>} />
              <Route path="/settings" element={<ProtectedLayout><Settings /></ProtectedLayout>} />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </WebSocketProvider>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
};

export default App;
