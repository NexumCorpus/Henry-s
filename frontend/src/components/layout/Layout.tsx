import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { useAppSelector } from '../../hooks/redux';
import Header from './Header';
import Sidebar from './Sidebar';
import ErrorBoundary from '../common/ErrorBoundary';

const Layout: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const { isDarkMode } = useAppSelector((state) => state.theme);

  // Apply theme to document root
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  // Close sidebar on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isSidebarOpen) {
        setIsSidebarOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isSidebarOpen]);

  const handleMenuToggle = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleSidebarClose = () => {
    setIsSidebarOpen(false);
  };

  return (
    <div className="layout">
      <Header 
        onMenuToggle={handleMenuToggle} 
        isSidebarOpen={isSidebarOpen}
      />
      
      <div className="layout__body">
        <Sidebar 
          isOpen={isSidebarOpen} 
          onClose={handleSidebarClose}
        />
        
        <main className="layout__main" role="main">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
};

export default Layout;