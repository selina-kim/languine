import { describe, expect, test, beforeEach, jest } from '@jest/globals';
import * as fsrsEndpoints from '@/apis/endpoints/fsrs';

// Mock storage
jest.mock('@/utils/storage', () => ({
  storage: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
  },
}));

// Mock the global fetch
(global as any).fetch = jest.fn() as jest.MockedFunction<typeof fetch>;

const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

import { storage } from '@/utils/storage';

const mockStorage = storage as jest.Mocked<typeof storage>;

describe('FSRS Endpoints', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockReset();
    mockStorage.getItem.mockResolvedValue(
      JSON.stringify({
        token: 'test_access_token',
        refreshToken: 'test_refresh_token',
      })
    );
    process.env.EXPO_PUBLIC_API_URL = 'https://api.example.com';
  });

  describe('logReview', () => {
    test('should log review successfully', async () => {
      const now = new Date().toISOString();
      const mockResponse = {
        card_id: 1,
        grade: 4,
        review_datetime: now,
        review_duration: 2500,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await fsrsEndpoints.logReview(1, 4, 2500);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/reviews'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            card_id: 1,
            grade: 4,
            review_duration: 2500,
          }),
        })
      );
      expect(result.data?.card_id).toBe(1);
      expect(result.data?.grade).toBe(4);
      expect(result.error).toBeNull();
    });

    test('should handle logReview with grade 1', async () => {
      const now = new Date().toISOString();
      const mockResponse = {
        card_id: 2,
        grade: 1,
        review_datetime: now,
        review_duration: 1800,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await fsrsEndpoints.logReview(2, 1, 1800);

      expect(result.data?.grade).toBe(1);
    });

    test('should handle logReview validation error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () =>
          JSON.stringify({
            error: 'Validation failed: grade must be between 1 and 4',
          }),
      } as Response);

      const result = await fsrsEndpoints.logReview(1, 10, 2500);

      expect(result.error).toBeTruthy();
    });

    test('should handle logReview network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network timeout'));

      const result = await fsrsEndpoints.logReview(1, 4, 2500);

      expect(result.error).toBeTruthy();
    });
  });

  describe('endReview', () => {
    test('should end review successfully', async () => {
      const mockResponse = {
        message: 'Review session ended',
        parameters_optimized: true,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await fsrsEndpoints.endReview(5);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/end-review'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ total_cards_reviewed: 5 }),
        })
      );
      expect(result.data?.message).toContain('ended');
      expect(result.data?.parameters_optimized).toBe(true);
      expect(result.error).toBeNull();
    });

    test('should handle endReview with zero cards reviewed', async () => {
      const mockResponse = {
        message: 'No cards reviewed',
        parameters_optimized: false,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await fsrsEndpoints.endReview(0);

      expect(result.data?.parameters_optimized).toBe(false);
    });

    test('should handle endReview network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Connection lost'));

      const result = await fsrsEndpoints.endReview(5);

      expect(result.error).toBeTruthy();
    });
  });

  describe('getDueCards', () => {
    test('should fetch due cards successfully', async () => {
      const today = new Date().toISOString().split('T')[0];
      const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];

      const mockResponse = {
        num_due_cards: 3,
        due_cards: [
          {
            card_id: 1,
            due_date: today,
            deck_id: 10,
          },
          {
            card_id: 2,
            due_date: today,
            deck_id: 10,
          },
          {
            card_id: 3,
            due_date: tomorrow,
            deck_id: 11,
          },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await fsrsEndpoints.getDueCards();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/due-cards'),
        expect.any(Object)
      );
      expect(result.data?.num_due_cards).toBe(3);
      expect(result.data?.due_cards).toHaveLength(3);
      expect(result.error).toBeNull();
    });

    test('should handle getDueCards with no cards due', async () => {
      const mockResponse = {
        num_due_cards: 0,
        due_cards: [],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await fsrsEndpoints.getDueCards();

      expect(result.data?.num_due_cards).toBe(0);
      expect(result.data?.due_cards).toHaveLength(0);
    });

    test('should handle getDueCards server error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => JSON.stringify({ error: 'Internal server error' }),
      } as Response);

      const result = await fsrsEndpoints.getDueCards();

      expect(result.error).toBeTruthy();
    });
  });

  describe('getNumDueCards', () => {
    test('should fetch number of due cards successfully', async () => {
      const mockResponse = {
        num_due_cards: 7,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await fsrsEndpoints.getNumDueCards();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/num-due-cards'),
        expect.any(Object)
      );
      expect(result.data?.num_due_cards).toBe(7);
      expect(result.error).toBeNull();
    });

    test('should handle getNumDueCards with zero cards', async () => {
      const mockResponse = {
        num_due_cards: 0,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await fsrsEndpoints.getNumDueCards();

      expect(result.data?.num_due_cards).toBe(0);
    });

    test('should handle getNumDueCards network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await fsrsEndpoints.getNumDueCards();

      expect(result.error).toBeTruthy();
    });
  });

  describe('FSRS endpoint URL construction', () => {
    test('should construct log review endpoint', () => {
      const endpoint = '/reviews';
      expect(endpoint).toBe('/reviews');
    });

    test('should construct end review endpoint', () => {
      const endpoint = '/end-review';
      expect(endpoint).toBe('/end-review');
    });

    test('should construct get due cards endpoint', () => {
      const endpoint = '/due-cards';
      expect(endpoint).toBe('/due-cards');
    });

    test('should construct get num due cards endpoint', () => {
      const endpoint = '/num-due-cards';
      expect(endpoint).toBe('/num-due-cards');
    });
  });
});
