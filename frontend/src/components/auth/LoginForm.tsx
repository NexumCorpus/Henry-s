import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { loginUser, clearError } from '../../store/slices/authSlice';
import LoadingSpinner from '../common/LoadingSpinner';

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  
  const { isLoading, error, isAuthenticated } = useAppSelector((state) => state.auth);

  const from = (location.state as any)?.from?.pathname || '/dashboard';

  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  useEffect(() => {
    // Clear error when component mounts
    dispatch(clearError());
  }, [dispatch]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    dispatch(loginUser({ email, password }));
  };

  return (
    <div className="login-form">
      <div className="login-form__container">
        <div className="login-form__header">
          <h1>Henry's SmartStock AI</h1>
          <p>Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form__form">
          {error && (
            <div className="login-form__error" role="alert">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email" className="form-group__label">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="form-group__input"
              required
              autoComplete="email"
              aria-describedby={error ? 'login-error' : undefined}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-group__label">
              Password
            </label>
            <div className="form-group__input-wrapper">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="form-group__input"
                required
                autoComplete="current-password"
                aria-describedby={error ? 'login-error' : undefined}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="form-group__toggle-password"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || !email || !password}
            className="login-form__submit"
          >
            {isLoading ? <LoadingSpinner size="small" message="Signing in..." /> : 'Sign In'}
          </button>
        </form>

        <div className="login-form__footer">
          <p>Demo Credentials:</p>
          <ul>
            <li>Manager: manager@henrys.com / password</li>
            <li>Bartender: bartender@henrys.com / password</li>
            <li>Barback: barback@henrys.com / password</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;