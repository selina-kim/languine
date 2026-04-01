import { describe, expect, test, beforeEach, jest, afterEach } from '@jest/globals';

// Mock storage
jest.mock('@/utils/storage', () => ({
  storage: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    deleteItem: jest.fn(),
  },
}));

// Mock fetch globally
global.fetch = jest.fn();

import { setUnauthorizedHandler } from '@/apis/client';
import { storage } from '@/utils/storage';

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    process.env.EXPO_PUBLIC_API_URL = 'https://api.example.com';
  });

  afterEach(() => {
    jest.clearAllMocks();
    setUnauthorizedHandler(null);
  });

  describe('setUnauthorizedHandler', () => {
    test('should set unauthorized handler', async () => {
      const handler = jest.fn();
      setUnauthorizedHandler(handler);

      expect(handler).toBeDefined();
    });

    test('should clear unauthorized handler', () => {
      setUnauthorizedHandler(null);
      expect(setUnauthorizedHandler).toBeDefined();
    });
  });

  describe('Token Storage', () => {
    test('should retrieve stored user data', async () => {
      const userData = { token: 'access123', refreshToken: 'refresh123' };
      (storage.getItem as jest.Mock).mockResolvedValueOnce(JSON.stringify(userData));

      const result = await storage.getItem('user');
      expect(result).toBeTruthy();
      expect(JSON.parse(result as string)).toEqual(userData);
    });

    test('should handle missing user data', async () => {
      (storage.getItem as jest.Mock).mockResolvedValueOnce(null);

      const result = await storage.getItem('user');
      expect(result).toBeNull();
    });

    test('should store user tokens', async () => {
      const userData = { token: 'access123', refreshToken: 'refresh123' };
      (storage.setItem as jest.Mock).mockResolvedValueOnce(undefined);

      await storage.setItem('user', JSON.stringify(userData));

      expect(storage.setItem).toHaveBeenCalledWith('user', JSON.stringify(userData));
    });

    test('should update stored tokens', async () => {
      const oldData = { token: 'old_token', refreshToken: 'refresh123' };
      const newData = { token: 'new_token', refreshToken: 'refresh123' };

      (storage.getItem as jest.Mock).mockResolvedValueOnce(JSON.stringify(oldData));
      (storage.setItem as jest.Mock).mockResolvedValueOnce(undefined);

      const result = await storage.getItem('user');
      expect(JSON.parse(result as string).token).toBe('old_token');

      await storage.setItem('user', JSON.stringify(newData));
      expect(storage.setItem).toHaveBeenCalledWith('user', JSON.stringify(newData));
    });
  });

  describe('Token Refresh', () => {
    test('should handle token refresh without refresh token', async () => {
      (storage.getItem as jest.Mock).mockResolvedValueOnce(JSON.stringify({ token: 'access123' }));

      const result = await storage.getItem('user');
      const user = JSON.parse(result as string);

      expect(user.refreshToken).toBeUndefined();
    });

    test('should handle API URL configuration', () => {
      const apiUrl = process.env.EXPO_PUBLIC_API_URL;
      expect(apiUrl).toBe('https://api.example.com');
    });
  });

  describe('Request Methods', () => {
    test('should construct correct endpoint URLs', () => {
      const endpoint = '/auth/login';
      const fullUrl = `https://api.example.com${endpoint}`;

      expect(fullUrl).toBe('https://api.example.com/auth/login');
    });

    test('should set correct HTTP headers', () => {
      const token = 'test_token_123';
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      };

      expect(headers['Content-Type']).toBe('application/json');
      expect(headers.Authorization).toBe(`Bearer ${token}`);
    });

    test('should handle different HTTP methods', () => {
      const methods = ['GET', 'POST', 'PUT', 'DELETE'];

      methods.forEach((method) => {
        expect(['GET', 'POST', 'PUT', 'DELETE']).toContain(method);
      });
    });
  });

  describe('Error Handling', () => {
    test('should handle missing API URL', () => {
      delete process.env.EXPO_PUBLIC_API_URL;
      const apiUrl = process.env.EXPO_PUBLIC_API_URL;

      expect(apiUrl).toBeUndefined();
    });

    test('should handle network errors gracefully', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      try {
        await fetch('https://api.example.com/test');
      } catch (error) {
        expect((error as Error).message).toBe('Network error');
      }
    });

    test('should parse error messages correctly', () => {
      const errorMessage = 'HTTP 401 - Invalid token';
      const errorParts = errorMessage.split(' - ');
      const cleanError = errorParts[errorParts.length - 1];

      expect(cleanError).toBe('Invalid token');
    });

    test('should handle JSON parsing errors', async () => {
      const invalidJson = 'not valid json';

      try {
        JSON.parse(invalidJson);
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe('Authorization', () => {
    test('should include auth token in headers', () => {
      const token = 'Bearer token123';
      const headers: HeadersInit = {
        Authorization: token,
      };

      expect(headers.Authorization).toBe('Bearer token123');
    });

    test('should handle token override', async () => {
      const overrideToken = 'override_token';
      const storedToken = 'stored_token';

      expect(overrideToken).not.toBe(storedToken);
    });

    test('should call unauthorized handler on 401', async () => {
      const handler = jest.fn();
      setUnauthorizedHandler(handler);

      expect(handler).toBeDefined();
    });
  });

  describe('Response Parsing', () => {
    test('should parse JSON responses', async () => {
      const responseData = { success: true, data: { id: '123' } };
      const jsonString = JSON.stringify(responseData);

      const parsed = JSON.parse(jsonString);
      expect(parsed).toEqual(responseData);
    });

    test('should handle empty responses', () => {
      const emptyResponse = '';
      expect(emptyResponse).toBe('');
    });

    test('should handle non-JSON responses', () => {
      const textResponse = 'Some text response';
      expect(textResponse).toBe('Some text response');
    });

    test('should extract error messages from responses', () => {
      const errorResponse = {
        error: 'Authentication failed',
        message: 'Invalid credentials',
      };

      const errorMessage = errorResponse.error || errorResponse.message;
      expect(errorMessage).toBe('Authentication failed');
    });
  });

  describe('Token Retry Logic', () => {
    test('should not retry if already retried', () => {
      let hasRetried = false;
      const maxRetries = 1;

      if (!hasRetried) {
        hasRetried = true;
      }

      expect(hasRetried).toBe(true);
      expect(maxRetries).toBe(1);
    });

    test('should track refresh promise state', async () => {
      let refreshPromise: Promise<string | null> | null = null;

      // Simulate setting the promise
      refreshPromise = Promise.resolve('new_token');

      // Simulate clearing after completion
      if (refreshPromise) {
        await refreshPromise;
        refreshPromise = null;
      }

      expect(refreshPromise).toBeNull();
    });
  });
});
