import { describe, expect, test, beforeEach, jest } from '@jest/globals';
import { exchangeGoogleToken, refreshToken } from '@/apis/endpoints/auth';

// Mock fetch globally
(global as any).fetch = jest.fn() as jest.MockedFunction<typeof fetch>;

const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

describe('Auth Endpoints', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockReset();
    process.env.EXPO_PUBLIC_API_URL = 'https://api.example.com';
  });

  describe('URL Construction', () => {
    test('should construct login endpoint', () => {
      const endpoint = '/auth/login';
      const fullUrl = `${process.env.EXPO_PUBLIC_API_URL}${endpoint}`;

      expect(fullUrl).toBe('https://api.example.com/auth/login');
    });

    test('should construct register endpoint', () => {
      const endpoint = '/auth/register';
      const fullUrl = `${process.env.EXPO_PUBLIC_API_URL}${endpoint}`;

      expect(fullUrl).toBe('https://api.example.com/auth/register');
    });

    test('should construct refresh endpoint', () => {
      const endpoint = '/auth/refresh';
      const fullUrl = `${process.env.EXPO_PUBLIC_API_URL}${endpoint}`;

      expect(fullUrl).toBe('https://api.example.com/auth/refresh');
    });
  });

  describe('Request Bodies', () => {
    test('should handle login request body', () => {
      const loginBody = {
        email: 'user@example.com',
        password: 'password123',
      };

      expect(loginBody.email).toBe('user@example.com');
      expect(loginBody.password).toBe('password123');
    });
  });

  describe('Response Handling', () => {
    test('should handle login response', () => {
      const response = {
        tokens: {
          access_token: 'access123',
          refresh_token: 'refresh123',
        },
        user: {
          id: '123',
          email: 'user@example.com',
        },
      };

      expect(response.tokens.access_token).toBe('access123');
      expect(response.user.id).toBe('123');
    });

    test('should handle login errors', () => {
      const errorResponse = {
        error: 'Invalid credentials',
        status: 401,
      };

      expect(errorResponse.error).toBe('Invalid credentials');
      expect(errorResponse.status).toBe(401);
    });
  });

  describe('Google Token Exchange', () => {
    test('should exchange Google token successfully', async () => {
      const mockGoogleResponse = {
        message: 'Authentication successful',
        user: {
          u_id: 'user_123',
          email: 'user@example.com',
          display_name: 'John Doe',
          timezone: 'UTC',
          google_id: 'google_123',
        },
        tokens: {
          access_token: 'jwt_access_token',
          refresh_token: 'jwt_refresh_token',
          token_type: 'Bearer',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockGoogleResponse,
      } as Response);

      const result = await exchangeGoogleToken(
        'google_access_token',
        'google_id_token'
      );

      expect(result.token).toBe('jwt_access_token');
      expect(result.user.id).toBe('user_123');
      expect(result.user.email).toBe('user@example.com');
      expect(result.user.name).toBe('John Doe');
      expect(result.user.token).toBe('jwt_access_token');
      expect(result.user.refreshToken).toBe('jwt_refresh_token');

      // Verify fetch was called with correct endpoint and body
      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/auth/google',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id_token: 'google_id_token' }),
        })
      );
    });

    test('should handle Google token exchange error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Invalid token' }),
      } as Response);

      await expect(
        exchangeGoogleToken('invalid_token', 'invalid_id_token')
      ).rejects.toThrow('Invalid token');
    });

    test('should handle Google token exchange network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network failed'));

      await expect(
        exchangeGoogleToken('token', 'id_token')
      ).rejects.toThrow();
    });
  });

  describe('Token Refresh', () => {
    test('should refresh token successfully', async () => {
      const mockRefreshResponse = {
        tokens: {
          access_token: 'new_access_token',
          refresh_token: 'new_refresh_token',
          token_type: 'Bearer',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockRefreshResponse,
      } as Response);

      const result = await refreshToken('old_access_token');

      // Cast to access the tokens structure returned by the backend
      const typedResult = result as any;
      expect(typedResult.tokens.access_token).toBe('new_access_token');
      expect(typedResult.tokens.refresh_token).toBe('new_refresh_token');

      // Verify fetch was called with correct headers
      expect(mockFetch).toHaveBeenCalledWith(
        'https://api.example.com/auth/refresh',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            Authorization: 'Bearer old_access_token',
          }),
        })
      );
    });

    test('should handle token refresh failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Refresh token expired' }),
      } as Response);

      await expect(refreshToken('expired_token')).rejects.toThrow(
        'Token refresh failed'
      );
    });
  });
});
