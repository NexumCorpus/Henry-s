import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAppSelector } from '../../hooks/redux';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  path: string;
  label: string;
  icon: string;
  roles?: string[];
}

const navItems: NavItem[] = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/inventory', label: 'Inventory', icon: '📦' },
  { path: '/scanning', label: 'Barcode Scanning', icon: '📱', roles: ['barback', 'bartender'] },
  { path: '/forecasting', label: 'Demand Forecasting', icon: '📈', roles: ['manager', 'admin'] },
  { path: '/orders', label: 'Orders', icon: '🛒', roles: ['manager', 'admin'] },
  { path: '/analytics', label: 'Analytics', icon: '📋', roles: ['manager', 'admin'] },
  { path: '/suppliers', label: 'Suppliers', icon: '🏢', roles: ['manager', 'admin'] },
  { path: '/settings', label: 'Settings', icon: '⚙️', roles: ['admin'] },
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user } = useAppSelector((state) => state.auth);

  const filteredNavItems = navItems.filter(item => 
    !item.roles || item.roles.includes(user?.role || '')
  );

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="sidebar__overlay"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      
      <aside 
        className={`sidebar ${isOpen ? 'sidebar--open' : ''}`}
        role="navigation"
        aria-label="Main navigation"
      >
        <nav className="sidebar__nav">
          <ul className="sidebar__nav-list">
            {filteredNavItems.map((item) => (
              <li key={item.path} className="sidebar__nav-item">
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `sidebar__nav-link ${isActive ? 'sidebar__nav-link--active' : ''}`
                  }
                  onClick={onClose}
                >
                  <span className="sidebar__nav-icon" aria-hidden="true">
                    {item.icon}
                  </span>
                  <span className="sidebar__nav-label">{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="sidebar__footer">
          <div className="sidebar__user-info">
            <div className="sidebar__user-name">{user?.name}</div>
            <div className="sidebar__user-role">{user?.role}</div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;