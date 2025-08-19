import { useEffect, useCallback } from 'react';
import { useAppDispatch, useAppSelector } from './redux';
import { websocketService } from '../services/websocketService';
import { setConnectionStatus, handleWebSocketMessage } from '../store/slices/inventorySlice';

export const useWebSocket = () => {
  const dispatch = useAppDispatch();
  const { token, isAuthenticated } = useAppSelector((state) => state.auth);
  const { isConnected } = useAppSelector((state) => state.inventory);

  const connect = useCallback(async () => {
    if (!token || !isAuthenticated) return;

    try {
      await websocketService.connect(token);
      dispatch(setConnectionStatus(true));
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      dispatch(setConnectionStatus(false));
    }
  }, [token, isAuthenticated, dispatch]);

  const disconnect = useCallback(() => {
    websocketService.disconnect();
    dispatch(setConnectionStatus(false));
  }, [dispatch]);

  useEffect(() => {
    if (isAuthenticated && token && !isConnected) {
      connect();
    } else if (!isAuthenticated && isConnected) {
      disconnect();
    }

    return () => {
      if (isConnected) {
        disconnect();
      }
    };
  }, [isAuthenticated, token, isConnected, connect, disconnect]);

  useEffect(() => {
    // Set up event handlers
    const handleConnection = () => {
      dispatch(setConnectionStatus(true));
    };

    const handleDisconnection = () => {
      dispatch(setConnectionStatus(false));
    };

    const handleStockUpdate = (message: any) => {
      dispatch(handleWebSocketMessage(message));
    };

    const handleTransaction = (message: any) => {
      dispatch(handleWebSocketMessage(message));
    };

    const handleAlert = (message: any) => {
      dispatch(handleWebSocketMessage(message));
    };

    // Register event handlers
    websocketService.on('connection', handleConnection);
    websocketService.on('disconnection', handleDisconnection);
    websocketService.on('stock_update', handleStockUpdate);
    websocketService.on('transaction', handleTransaction);
    websocketService.on('alert', handleAlert);

    // Cleanup
    return () => {
      websocketService.off('connection', handleConnection);
      websocketService.off('disconnection', handleDisconnection);
      websocketService.off('stock_update', handleStockUpdate);
      websocketService.off('transaction', handleTransaction);
      websocketService.off('alert', handleAlert);
    };
  }, [dispatch]);

  return {
    isConnected,
    connect,
    disconnect,
  };
};