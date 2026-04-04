import { describe, expect, test, beforeEach, jest } from '@jest/globals';
import * as cardEndpoints from '@/apis/endpoints/cards';

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

describe('Card Endpoints', () => {
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

  describe('getCards', () => {
    test('should fetch cards with default pagination', async () => {
      const mockResponse = {
        cards: [
          {
            c_id: 1,
            word: 'Test',
            translation: 'Answer',
            difficulty: 1,
            stability: 0.5,
            learning_state: 0,
            due_date: null,
            word_example: null,
            trans_example: null,
            word_roman: null,
            trans_roman: null,
            image: null,
          },
        ],
        pagination: {
          page: 1,
          per_page: 50,
          total: 1,
          total_pages: 1,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await cardEndpoints.getCards('deck123');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/decks/deck123/cards?page=1&per_page=50'),
        expect.any(Object)
      );
      expect(result.data).toEqual(mockResponse);
      expect(result.error).toBeNull();
    });

    test('should fetch cards with custom pagination', async () => {
      const mockResponse = {
        cards: [],
        pagination: {
          page: 2,
          per_page: 25,
          total: 100,
          total_pages: 4,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await cardEndpoints.getCards('deck123', 2, 25);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/decks/deck123/cards?page=2&per_page=25'),
        expect.any(Object)
      );
      expect(result.data.pagination.page).toBe(2);
    });

    test('should handle getCards error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ error: 'Deck not found' }),
      } as Response);

      const result = await cardEndpoints.getCards('invalid');

      expect(result.error).toBeTruthy();
    });
  });

  describe('getCard', () => {
    test('should fetch single card successfully', async () => {
      const mockCard = {
        c_id: 1,
        word: 'Front text',
        translation: 'Back text',
        difficulty: 3,
        stability: 0.8,
        learning_state: 2,
        due_date: null,
        word_example: null,
        trans_example: null,
        word_roman: null,
        trans_roman: null,
        image: null,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockCard),
      } as Response);

      const result = await cardEndpoints.getCard('deck123', 'card456');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/decks/deck123/cards/card456'),
        expect.any(Object)
      );
      expect(result.data).toEqual(mockCard);
      expect(result.error).toBeNull();
    });

    test('should handle getCard not found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ error: 'Card not found' }),
      } as Response);

      const result = await cardEndpoints.getCard('deck123', 'invalid');

      expect(result.error).toBeTruthy();
    });
  });

  describe('createCard', () => {
    test('should create card successfully', async () => {
      const createPayload = {
        word: '新しい',
        translation: 'New',
        image: 'img123',
      };

      const mockResponse = {
        message: 'Card created successfully',
        card: {
          c_id: 1,
          word: '新しい',
          translation: 'New',
          image: 'img123',
          difficulty: 0,
          stability: 0,
          learning_state: 0,
          due_date: null,
          word_example: null,
          trans_example: null,
          word_roman: null,
          trans_roman: null,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await cardEndpoints.createCard('deck123', createPayload);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/decks/deck123/card'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(createPayload),
        })
      );
      expect(result.data.card.c_id).toBe(1);
      expect(result.error).toBeNull();
    });

    test('should handle createCard validation error', async () => {
      const invalidPayload = {
        word: '',
        translation: 'Missing word',
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () =>
          JSON.stringify({
            error: 'Validation failed: word is required',
          }),
      } as Response);

      const result = await cardEndpoints.createCard(
        'deck123',
        invalidPayload as any
      );

      expect(result.error).toBeTruthy();
    });

    test('should handle createCard network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network timeout'));

      const result = await cardEndpoints.createCard('deck123', {
        word: 'test',
        translation: 'test',
      });

      expect(result.error).toBeTruthy();
    });
  });

  describe('updateCard', () => {
    test('should update card successfully', async () => {
      const updatePayload = {
        word: '更新',
        translation: 'Updated',
      };

      const mockResponse = {
        message: 'Card updated successfully',
        card: {
          c_id: 1,
          word: '更新',
          translation: 'Updated',
          difficulty: 3,
          stability: 0.8,
          learning_state: 2,
          due_date: null,
          word_example: null,
          trans_example: null,
          word_roman: null,
          trans_roman: null,
          image: null,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await cardEndpoints.updateCard(
        'deck123',
        'card456',
        updatePayload
      );

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/decks/deck123/cards/card456'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(updatePayload),
        })
      );
      expect(result.data.card.word).toBe('更新');
      expect(result.error).toBeNull();
    });

    test('should handle updateCard card not found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ error: 'Card not found' }),
      } as Response);

      const result = await cardEndpoints.updateCard('deck123', 'invalid', {
        word: 'test',
        translation: 'test',
      });

      expect(result.error).toBeTruthy();
    });
  });

  describe('deleteCard', () => {
    test('should delete card successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ message: 'Card deleted successfully' }),
      } as Response);

      const result = await cardEndpoints.deleteCard('deck123', 'card456');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/decks/deck123/cards/card456'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
      expect(result.data.message).toContain('deleted');
      expect(result.error).toBeNull();
    });

    test('should handle deleteCard not found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ error: 'Card not found' }),
      } as Response);

      const result = await cardEndpoints.deleteCard('deck123', 'invalid');

      expect(result.error).toBeTruthy();
    });

    test('should handle deleteCard error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => JSON.stringify({ error: 'Failed to delete card' }),
      } as Response);

      const result = await cardEndpoints.deleteCard('deck123', 'card456');

      expect(result.error).toBeTruthy();
    });
  });

  describe('getReviewCards', () => {
    test('should fetch review cards with default limit', async () => {
      const mockResponse = {
        cards: [
          {
            c_id: 1,
            word: 'Test 1',
            translation: 'Answer 1',
            difficulty: 2,
            stability: 0.6,
            learning_state: 1,
            due_date: new Date().toISOString(),
            word_example: null,
            trans_example: null,
            word_roman: null,
            trans_roman: null,
            image: null,
          },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await cardEndpoints.getReviewCards('deck123');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/decks/deck123/review?limit=20'),
        expect.any(Object)
      );
      expect(result.data.cards).toHaveLength(1);
      expect(result.error).toBeNull();
    });

    test('should fetch review cards with custom limit', async () => {
      const mockResponse = { cards: [] };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await cardEndpoints.getReviewCards('deck123', 50);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/decks/deck123/review?limit=50'),
        expect.any(Object)
      );
    });

    test('should handle getReviewCards error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ error: 'Deck not found' }),
      } as Response);

      const result = await cardEndpoints.getReviewCards('invalid');

      expect(result.error).toBeTruthy();
    });
  });

  describe('Card endpoint URL construction', () => {
    test('should construct get cards endpoint with pagination params', () => {
      const deckId = '123';
      const page = 2;
      const perPage = 25;
      const endpoint = `/decks/${deckId}/cards?page=${page}&per_page=${perPage}`;

      expect(endpoint).toBe('/decks/123/cards?page=2&per_page=25');
    });

    test('should construct create card endpoint correctly', () => {
      const deckId = '123';
      const endpoint = `/decks/${deckId}/card`;

      expect(endpoint).toBe('/decks/123/card');
    });

    test('should construct update card endpoint correctly', () => {
      const deckId = '123';
      const cardId = '456';
      const endpoint = `/decks/${deckId}/cards/${cardId}`;

      expect(endpoint).toBe('/decks/123/cards/456');
    });

    test('should construct delete card endpoint correctly', () => {
      const deckId = '123';
      const cardId = '456';
      const endpoint = `/decks/${deckId}/cards/${cardId}`;

      expect(endpoint).toBe('/decks/123/cards/456');
    });
  });
});
