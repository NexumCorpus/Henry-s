import React from 'react';

interface ConnectionStatusProps {
  isConnected: boolean;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ isConnected }) => {
  return (
    <div className={`connection-status connection-status--${isConnected ? 'connected' : 'disconnected'}`}>
      <div className="connection-status__indicator"></div>
      <span className="connection-status__text">
        {isConnected ? 'Live Updates' : 'Offline'}
      </span>
    </div>
  );
};

export default ConnectionStatus;