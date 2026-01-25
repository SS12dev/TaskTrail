/**
 * React WebSocket Hook for A2A Streaming
 *
 * Manages WebSocket connection for real-time A2A task updates with automatic
 * authentication, reconnection, and message handling.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { auth } from '../firebase';

export interface WebSocketMessage {
  type: 'connected' | 'state_change' | 'output_chunk' | 'error' | 'task_complete' | 'agent_switch' | 'pong';
  contextId: string;
  taskId?: string;
  data?: any;
  timestamp?: string;
}

export interface UseWebSocketOptions {
  contextId: string;
  enabled?: boolean;
  onMessage?: (message: WebSocketMessage) => void;
  onStateChange?: (taskId: string, state: string, message?: string) => void;
  onOutputChunk?: (chunk: string) => void;
  onError?: (error: string) => void;
  onConnected?: () => void;
  onDisconnected?: () => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  sendMessage: (message: any) => void;
  disconnect: () => void;
  reconnect: () => void;
}

export function useWebSocket({
  contextId,
  enabled = true,
  onMessage,
  onStateChange,
  onOutputChunk,
  onError,
  onConnected,
  onDisconnected,
  autoReconnect = true,
  reconnectInterval = 3000,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const shouldConnectRef = useRef(enabled);

  // Get WebSocket URL from environment
  const getWebSocketUrl = useCallback(async () => {
    // Get Firebase auth token
    const user = auth.currentUser;
    if (!user) {
      throw new Error('User not authenticated');
    }

    const token = await user.getIdToken();

    // Build WebSocket URL
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    return `${wsUrl}/a2a/v1/ws/${contextId}?token=${encodeURIComponent(token)}`;
  }, [contextId]);

  // Send message through WebSocket
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }, []);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      // Call generic message handler
      onMessage?.(message);

      // Call specific handlers based on message type
      switch (message.type) {
        case 'connected':
          console.log('WebSocket connected:', message.contextId);
          setIsConnected(true);
          setIsConnecting(false);
          setError(null);
          onConnected?.();
          break;

        case 'state_change':
          console.log('Task state change:', message.data);
          if (message.taskId && message.data?.taskState) {
            onStateChange?.(message.taskId, message.data.taskState, message.data.message);
          }
          break;

        case 'output_chunk':
          console.log('Output chunk received');
          if (message.data?.chunk) {
            onOutputChunk?.(message.data.chunk);
          }
          break;

        case 'error':
          console.error('WebSocket error message:', message.data);
          const errorMsg = message.data?.error || 'Unknown error';
          setError(errorMsg);
          onError?.(errorMsg);
          break;

        case 'task_complete':
          console.log('Task completed:', message.data);
          break;

        case 'agent_switch':
          console.log('Agent switch:', message.data);
          break;

        case 'pong':
          // Heartbeat response
          break;

        default:
          console.log('Unknown message type:', message.type);
      }
    } catch (err) {
      console.error('Error parsing WebSocket message:', err);
    }
  }, [onMessage, onStateChange, onOutputChunk, onError, onConnected]);

  // Setup ping interval to keep connection alive
  const setupPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }

    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'ping' });
      }
    }, 20000); // Ping every 20 seconds
  }, [sendMessage]);

  // Connect to WebSocket
  const connect = useCallback(async () => {
    if (!shouldConnectRef.current) {
      return;
    }

    // Don't connect if already connecting or connected
    if (isConnecting || isConnected) {
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const url = await getWebSocketUrl();
      console.log('Connecting to WebSocket:', url);

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connection opened');
        setupPingInterval();
      };

      ws.onmessage = handleMessage;

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
        setIsConnecting(false);
      };

      ws.onclose = (event) => {
        console.log('WebSocket connection closed:', event.code, event.reason);
        setIsConnected(false);
        setIsConnecting(false);
        onDisconnected?.();

        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }

        // Attempt reconnection if enabled and should connect
        if (autoReconnect && shouldConnectRef.current && event.code !== 1000) {
          console.log(`Reconnecting in ${reconnectInterval}ms...`);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
    } catch (err) {
      console.error('Error connecting to WebSocket:', err);
      setError(err instanceof Error ? err.message : 'Connection failed');
      setIsConnecting(false);
    }
  }, [
    isConnecting,
    isConnected,
    getWebSocketUrl,
    handleMessage,
    setupPingInterval,
    autoReconnect,
    reconnectInterval,
    onDisconnected,
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    shouldConnectRef.current = false;

    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Clear ping interval
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnected');
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  // Reconnect (manual)
  const reconnect = useCallback(() => {
    disconnect();
    shouldConnectRef.current = true;
    setTimeout(() => {
      connect();
    }, 100);
  }, [disconnect, connect]);

  // Effect to manage connection lifecycle
  useEffect(() => {
    shouldConnectRef.current = enabled;

    if (enabled) {
      connect();
    } else {
      disconnect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [enabled, contextId]); // Reconnect if contextId changes

  return {
    isConnected,
    isConnecting,
    error,
    sendMessage,
    disconnect,
    reconnect,
  };
}
