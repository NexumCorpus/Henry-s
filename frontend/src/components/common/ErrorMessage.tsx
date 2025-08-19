import React from 'react';

interface ErrorMessageProps {
  message: string;
  onDismiss?: () => void;
  type?: 'error' | 'warning' | 'info';
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ 
  message, 
  onDismiss, 
  type = 'error' 
}) => {
  return (
    <div className={`error-message error-message--${type}`}>
      <div className="error-message__content">
        <div className="error-message__icon">
          {type === 'error' && '❌'}
          {type === 'warning' && '⚠️'}
          {type === 'info' && 'ℹ️'}
        </div>
        <span className="error-message__text">{message}</span>
      </div>
      {onDismiss && (
        <button 
          className="error-message__dismiss"
          onClick={onDismiss}
          aria-label="Dismiss"
        >
          ×
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;