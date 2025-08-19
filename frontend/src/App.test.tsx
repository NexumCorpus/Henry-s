import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './store/slices/authSlice';
import themeReducer from './store/slices/themeSlice';
import App from './App';

// Create a test store
const createTestStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      theme: themeReducer,
    },
    preloadedState: initialState,
  });
};

// Mock the authAPI to prevent actual API calls during tests
jest.mock('./services/authAPI', () => ({
  authAPI: {
    login: jest.fn(),
    logout: jest.fn(),
    verifyToken: jest.fn(),
  },
}));

describe('App', () => {
  it('renders login form when not authenticated', () => {
    const store = createTestStore({
      auth: {
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      },
      theme: {
        isDarkMode: false,
      },
    });

    render(
      <Provider store={store}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </Provider>
    );

    expect(screen.getByText("Henry's SmartStock AI")).toBeInTheDocument();
    expect(screen.getByText('Sign in to your account')).toBeInTheDocument();
  });

  it('renders dashboard when authenticated', () => {
    const store = createTestStore({
      auth: {
        user: {
          id: '1',
          email: 'test@henrys.com',
          name: 'Test User',
          role: 'manager',
          permissions: [],
        },
        token: 'test-token',
        isAuthenticated: true,
        isLoading: false,
        error: null,
      },
      theme: {
        isDarkMode: false,
      },
    });

    render(
      <Provider store={store}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </Provider>
    );

    expect(screen.getByText('Welcome back, Test User!')).toBeInTheDocument();
  });
});