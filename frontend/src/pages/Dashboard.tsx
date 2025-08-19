import React from 'react';
import { useAppSelector } from '../hooks/redux';

const Dashboard: React.FC = () => {
  const { user } = useAppSelector((state) => state.auth);

  const getRoleSpecificContent = () => {
    switch (user?.role) {
      case 'barback':
        return (
          <div className="dashboard__role-content">
            <h2>Barback Dashboard</h2>
            <div className="dashboard__cards">
              <div className="dashboard__card">
                <h3>Quick Scan</h3>
                <p>Scan items to update inventory</p>
                <button className="dashboard__card-action">Start Scanning</button>
              </div>
              <div className="dashboard__card">
                <h3>Low Stock Alerts</h3>
                <p>Items needing attention</p>
                <span className="dashboard__card-badge">3 items</span>
              </div>
            </div>
          </div>
        );
      case 'bartender':
        return (
          <div className="dashboard__role-content">
            <h2>Bartender Dashboard</h2>
            <div className="dashboard__cards">
              <div className="dashboard__card">
                <h3>Current Stock</h3>
                <p>Real-time inventory levels</p>
                <button 
                  className="dashboard__card-action"
                  onClick={() => window.location.href = '/inventory'}
                >
                  View Inventory
                </button>
              </div>
              <div className="dashboard__card">
                <h3>Pour Tracking</h3>
                <p>Log usage during shift</p>
                <button className="dashboard__card-action">Log Pours</button>
              </div>
            </div>
          </div>
        );
      case 'manager':
      case 'admin':
        return (
          <div className="dashboard__role-content">
            <h2>Management Dashboard</h2>
            <div className="dashboard__cards">
              <div className="dashboard__card">
                <h3>Inventory Management</h3>
                <p>Real-time stock levels and adjustments</p>
                <button 
                  className="dashboard__card-action"
                  onClick={() => window.location.href = '/inventory'}
                >
                  Manage Inventory
                </button>
              </div>
              <div className="dashboard__card">
                <h3>Analytics Overview</h3>
                <p>KPIs and performance metrics</p>
                <button className="dashboard__card-action">View Analytics</button>
              </div>
              <div className="dashboard__card">
                <h3>Automated Orders</h3>
                <p>Review pending orders</p>
                <span className="dashboard__card-badge">2 pending</span>
              </div>
              <div className="dashboard__card">
                <h3>Demand Forecast</h3>
                <p>AI-powered predictions</p>
                <button className="dashboard__card-action">View Forecasts</button>
              </div>
            </div>
          </div>
        );
      default:
        return <div>Welcome to Henry's SmartStock AI</div>;
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard__header">
        <h1>Welcome back, {user?.name}!</h1>
        <p className="dashboard__subtitle">
          Here's what's happening at Henry's on Market today
        </p>
      </div>

      {getRoleSpecificContent()}

      <div className="dashboard__quick-stats">
        <div className="dashboard__stat">
          <span className="dashboard__stat-value">156</span>
          <span className="dashboard__stat-label">Items in Stock</span>
        </div>
        <div className="dashboard__stat">
          <span className="dashboard__stat-value">$12,450</span>
          <span className="dashboard__stat-label">Inventory Value</span>
        </div>
        <div className="dashboard__stat">
          <span className="dashboard__stat-value">98.5%</span>
          <span className="dashboard__stat-label">Service Level</span>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;