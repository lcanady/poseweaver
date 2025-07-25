/**
 * React hook for managing WebSocket connections and description generation.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '@/contexts/auth-context';
import websocketService, { 
  DescriptionRequest, 
  DescriptionResult, 
  ProgressUpdate, 
  ErrorResponse 
} from '@/utils/websocket-service';

export interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  connectionError: string | null;
  generateDescription: (request: DescriptionRequest) => Promise<void>;
  isGenerating: boolean;
  progress: ProgressUpdate | null;
  result: DescriptionResult | null;
  error: string | null;
  clearResult: () => void;
  clearError: () => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const { user, getToken } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [result, setResult] = useState<DescriptionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const connectionAttempted = useRef(false);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);

  // Connect to WebSocket when user is available
  const connect = useCallback(async () => {
    if (!user || isConnecting || isConnected) return;

    setIsConnecting(true);
    setConnectionError(null);

    try {
      const token = getToken();
      if (!token) {
        throw new Error('No authentication token available');
      }

      const success = await websocketService.connect(token);
      
      if (success) {
        setIsConnected(true);
        setConnectionError(null);
        console.log('WebSocket connected successfully');
      } else {
        throw new Error('Failed to establish WebSocket connection');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Connection failed';
      setConnectionError(errorMessage);
      console.error('WebSocket connection error:', errorMessage);
      
      // Schedule reconnection attempt
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
      reconnectTimer.current = setTimeout(() => {
        if (user && !isConnected) {
          connect();
        }
      }, 5000);
    } finally {
      setIsConnecting(false);
    }
  }, [user, isConnecting, isConnected, getToken]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    websocketService.disconnect();
    setIsConnected(false);
    setIsConnecting(false);
    setConnectionError(null);
    
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
  }, []);

  // Generate description via WebSocket
  const generateDescription = useCallback(async (request: DescriptionRequest) => {
    if (!isConnected) {
      setError('WebSocket not connected. Please try again.');
      return;
    }

    setIsGenerating(true);
    setProgress(null);
    setResult(null);
    setError(null);

    try {
      await websocketService.generateDescription(request, {
        onProgress: (progressData) => {
          setProgress(progressData);
        },
        onComplete: (resultData) => {
          setResult(resultData);
          setIsGenerating(false);
          setProgress(null);
        },
        onError: (errorData) => {
          setError(errorData.error);
          setIsGenerating(false);
          setProgress(null);
        }
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Generation failed';
      setError(errorMessage);
      setIsGenerating(false);
      setProgress(null);
    }
  }, [isConnected]);

  // Clear result
  const clearResult = useCallback(() => {
    setResult(null);
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Auto-connect when user is available
  useEffect(() => {
    if (user && !connectionAttempted.current) {
      connectionAttempted.current = true;
      connect();
    } else if (!user && isConnected) {
      disconnect();
      connectionAttempted.current = false;
    }

    return () => {
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
    };
  }, [user, connect, disconnect, isConnected]);

  // Check connection status periodically
  useEffect(() => {
    if (!user) return;

    const checkConnection = () => {
      const socketConnected = websocketService.isSocketConnected();
      if (isConnected !== socketConnected) {
        setIsConnected(socketConnected);
        
        // If we think we're connected but socket says we're not, try to reconnect
        if (isConnected && !socketConnected) {
          connect();
        }
      }
    };

    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, [user, isConnected, connect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    isConnecting,
    connectionError,
    generateDescription,
    isGenerating,
    progress,
    result,
    error,
    clearResult,
    clearError
  };
}
