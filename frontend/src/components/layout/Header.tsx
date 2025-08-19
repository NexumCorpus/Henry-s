import React from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { logoutUser } from '../../store/slices/authSlice';
import { toggleTheme } from '../../store/slices/themeSlice';

interface HeaderProps {
  onMenuToggle: () => void;
  isSidebarOpen: boolean;
}

const Header: React.FC<HeaderProps> = ({ onMenuToggle, isSidebarOpen }) => {
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);
  const { isDarkMode } = useAppSelector((state) => state.theme);

  const handleLogout = () => {
    dispatch(logoutUser());
  };

  const handleThemeToggle = () => {
    dispatch(toggleTheme());
  };

  return (
    <header className="header" role="banner">
      <div className="header__left">
        <button
          onClick={onMenuToggle}
          className="header__menu-toggle"
          aria-label={isSidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          aria-expanded={isSidebarOpen}
        >
          <span className="header__menu-icon">
            {isSidebarOpen ? '✕' : '☰'}
          </span>
        </button>
        <h1 className="header__title">Henry's SmartStock AI</h1>
      </div>

      <div className="header__right">
        <button
          onClick={handleThemeToggle}
          className="header__theme-toggle"
          aria-label={`Switch to ${isDarkMode ? 'light' : 'dark'} mode`}
          title={`Switch to ${isDarkMode ? 'light' : 'dark'} mode`}
        >
          {isDarkMode ? '☀️' : '🌙'}
        </button>

        <div className="header__user">
          <span className="header__user-name">{user?.name}</span>
          <span className="header__user-role">{user?.role}</span>
        </div>

        <button
          onClick={handleLogout}
          className="header__logout"
          aria-label="Sign out"
          title="Sign out"
        >
          Sign Out
        </button>
      </div>
    </header>
  );
};

export default Header;