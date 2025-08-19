import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { verifyToken } from '../../store/slices/authSlice';
import LoadingSpinner from '../common/LoadingSpinner';

interface AuthProviderProps {
  children: React.ReactNode;
}

const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const dispatch = useAppDispatch();
  const { token, isLoading, isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    // Verify token on app startup if token exists
    if (token && !isAuthenticated) {
      dispatch(verifyToken());
    }
  }, [dispatch, token, isAuthenticated]);

  // Show loading spinner while verifying token
  if (token && isLoading && !isAuthenticated) {
    return (
      <div className="auth-provider__loading">
        <LoadingSpinner size="large" message="Initializing application..." />
      </div>
    );
  }

  return <>{children}</>;
};

export default AuthProvider;