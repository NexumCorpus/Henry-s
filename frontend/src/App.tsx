import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';
import AuthProvider from './components/auth/AuthProvider';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Layout from './components/layout/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import ErrorBoundary from './components/common/ErrorBoundary';
import './App.css';
import './styles/common.css';
import './styles/inventory.css';
import './styles/adjustment-modal.css';

function App() {
  return (
    <Provider store={store}>
      <Router>
        <ErrorBoundary>
          <AuthProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              
              {/* Protected routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                
                {/* Inventory Management */}
                <Route path="inventory" element={<Inventory />} />
                <Route path="scanning" element={<div>Barcode Scanning - Coming Soon</div>} />
                <Route path="forecasting" element={<div>Demand Forecasting - Coming Soon</div>} />
                <Route path="orders" element={<div>Orders Management - Coming Soon</div>} />
                <Route path="analytics" element={<div>Analytics Dashboard - Coming Soon</div>} />
                <Route path="suppliers" element={<div>Supplier Management - Coming Soon</div>} />
                <Route path="settings" element={<div>Settings - Coming Soon</div>} />
              </Route>
              
              {/* Catch all route */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </AuthProvider>
        </ErrorBoundary>
      </Router>
    </Provider>
  );
}

export default App;