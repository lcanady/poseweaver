/**
 * WebSocket service for real-time communication with backend.
 * Handles description generation and other long-running operations without HTTP timeouts.
 */

import { io, Socket } from 'socket.io-client';

export interface DescriptionRequest {
  image_data: string; // base64 encoded image
  image_format: string;
  user_prompt: string;
  description_style: 'minimal' | 'balanced' | 'elaborate';
  focus_areas?: string[];
}

export interface DescriptionResult {
  description: string;
  style: string;
  prompt_used: string;
  model_used: string;
  timestamp: string;
  word_count: number;
  processing_time_ms: number;
}

export interface ProgressUpdate {
  status: 'starting' | 'processing' | 'complete';
  message: string;
}

export interface ErrorResponse {
  error: string;
  usage_info?: any;
}

export type DescriptionEventHandler = {
  onProgress?: (progress: ProgressUpdate) => void;
  onComplete?: (result: DescriptionResult) => void;
  onError?: (error: ErrorResponse) => void;
};

class WebSocketService {
  private socket: Socket | null = null;
  private isConnected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second

  constructor() {
    this.connect = this.connect.bind(this);
    this.disconnect = this.disconnect.bind(this);
    this.generateDescription = this.generateDescription.bind(this);
  }

  /**
   * Connect to WebSocket server with authentication
   */
  async connect(token: string): Promise<boolean> {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
      
      // Disconnect existing connection if any
      if (this.socket) {
        this.socket.disconnect();
      }

      // Create new socket connection with authentication
      this.socket = io(backendUrl, {
        auth: {
          token: token
        },
        transports: ['websocket', 'polling'],
        timeout: 10000,
        forceNew: true
      });

      // Set up connection event handlers
      this.setupConnectionHandlers();

      // Wait for connection
      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          console.error('WebSocket connection timeout');
          resolve(false);
        }, 10000);

        this.socket!.on('connected', () => {
          clearTimeout(timeout);
          this.isConnected = true;
          this.reconnectAttempts = 0;
          console.log('WebSocket connected successfully');
          resolve(true);
        });

        this.socket!.on('connect_error', (error) => {
          clearTimeout(timeout);
          console.error('WebSocket connection error:', error);
          resolve(false);
        });
      });

    } catch (error) {
      console.error('WebSocket connection failed:', error);
      return false;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.isConnected = false;
  }

  /**
   * Check if WebSocket is connected
   */
  isSocketConnected(): boolean {
    return this.isConnected && this.socket?.connected === true;
  }

  /**
   * Generate description via WebSocket
   */
  async generateDescription(
    request: DescriptionRequest,
    handlers: DescriptionEventHandler
  ): Promise<void> {
    if (!this.socket || !this.isConnected) {
      handlers.onError?.({ error: 'WebSocket not connected' });
      return;
    }

    try {
      // Set up event handlers for this request
      const handleProgress = (data: ProgressUpdate) => {
        handlers.onProgress?.(data);
      };

      const handleComplete = (data: { status: string; result: DescriptionResult }) => {
        if (data.status === 'success') {
          handlers.onComplete?.(data.result);
        } else {
          handlers.onError?.({ error: 'Unexpected response format' });
        }
        // Clean up event listeners
        this.socket!.off('description_progress', handleProgress);
        this.socket!.off('description_complete', handleComplete);
        this.socket!.off('description_error', handleError);
      };

      const handleError = (data: ErrorResponse) => {
        handlers.onError?.(data);
        // Clean up event listeners
        this.socket!.off('description_progress', handleProgress);
        this.socket!.off('description_complete', handleComplete);
        this.socket!.off('description_error', handleError);
      };

      // Register event handlers
      this.socket.on('description_progress', handleProgress);
      this.socket.on('description_complete', handleComplete);
      this.socket.on('description_error', handleError);

      // Send description generation request
      this.socket.emit('generate_description', request);

    } catch (error) {
      console.error('Error sending description request:', error);
      handlers.onError?.({ error: 'Failed to send request' });
    }
  }

  /**
   * Set up connection event handlers
   */
  private setupConnectionHandlers(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.isConnected = true;
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.isConnected = false;
      
      // Attempt reconnection for certain disconnect reasons
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, don't reconnect
        return;
      }
      
      this.attemptReconnect();
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.isConnected = false;
      this.attemptReconnect();
    });
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      if (this.socket && !this.socket.connected) {
        this.socket.connect();
      }
    }, delay);
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();
export default websocketService;
