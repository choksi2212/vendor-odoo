import { WS_BASE_URL } from '../config';
import { tokenManager } from './client';

class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: ((data: any) => void)[] = [];
  private reconnectTimeout: NodeJS.Timeout | null = null;

  connect(): void {
    const token = tokenManager.getAccessToken();
    if (!token) {
      console.warn('WebSocket: No access token available');
      return;
    }

    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/api/ws/notifications?token=${token}`);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'notification') {
            this.listeners.forEach((fn) => fn(data.data));
          }
        } catch (err) {
          console.error('WebSocket message parse error:', err);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Reconnect after 5 seconds
        this.reconnectTimeout = setTimeout(() => this.connect(), 5000);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (err) {
      console.error('WebSocket connection error:', err);
    }
  }

  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    this.ws?.close();
    this.ws = null;
    this.listeners = [];
  }

  onNotification(callback: (data: any) => void): () => void {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((fn) => fn !== callback);
    };
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();
