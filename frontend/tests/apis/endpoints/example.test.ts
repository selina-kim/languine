import { describe, expect, test, beforeEach, jest } from '@jest/globals';
import * as exampleEndpoints from '@/apis/endpoints/example';

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

describe('Example Endpoints (Dictionary)', () => {
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

  describe('getWordDefinition', () => {
    test('should fetch word definition successfully', async () => {
      const mockResponse = {
        word: 'hello',
        definitions: [
          {
            definition: 'A polite greeting expressing one\'s good wishes',
            example_sentences: ['Hello, how are you?', 'She greeted us with a hello.'],
          },
        ],
        pronunciation: 'həˈlō',
        audio_url: 'https://example.com/audio/hello.mp3',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await exampleEndpoints.getWordDefinition('hello');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/define/hello'),
        expect.any(Object)
      );
      expect(result.data?.word).toBe('hello');
      expect(result.data?.definitions).toHaveLength(1);
      expect(result.data?.pronunciation).toBe('həˈlō');
      expect(result.error).toBeNull();
    });

    test('should fetch word with multiple definitions', async () => {
      const mockResponse = {
        word: 'read',
        definitions: [
          {
            definition: 'To look at and comprehend the meaning of (written or printed characters, words, or sentences)',
            example_sentences: ['I read the book yesterday.'],
          },
          {
            definition: 'Present tense form of read',
            example_sentences: ['She reads every day.'],
          },
        ],
        pronunciation: 'rēd',
        audio_url: 'https://example.com/audio/read.mp3',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await exampleEndpoints.getWordDefinition('read');

      expect(result.data?.definitions).toHaveLength(2);
      expect(result.data?.definitions[0].example_sentences).toHaveLength(1);
    });

    test('should handle word with special characters', async () => {
      const mockResponse = {
        word: 'café',
        definitions: [
          {
            definition: 'A small restaurant selling light refreshments',
            example_sentences: ['Let\'s meet at the café.'],
          },
        ],
        pronunciation: 'kə-ˈfā',
        audio_url: 'https://example.com/audio/cafe.mp3',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await exampleEndpoints.getWordDefinition('café');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/define/caf%C3%A9'),
        expect.any(Object)
      );
      expect(result.data?.word).toBe('café');
    });

    test('should include suggestions for similar words', async () => {
      const mockResponse = {
        word: 'helo',
        definitions: [],
        pronunciation: null,
        audio_url: null,
        suggestions: ['hello', 'held', 'help'],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await exampleEndpoints.getWordDefinition('helo');

      expect(result.data?.suggestions).toEqual(['hello', 'held', 'help']);
    });

    test('should handle word not found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ error: 'Word not found' }),
      } as Response);

      const result = await exampleEndpoints.getWordDefinition('zzzzqqqq');

      expect(result.error).toBeTruthy();
    });

    test('should handle null pronunciation and audio_url', async () => {
      const mockResponse = {
        word: 'xyz',
        definitions: [
          {
            definition: 'A variable or unknown quantity',
            example_sentences: ['In algebra, x, y, and z are commonly used.'],
          },
        ],
        pronunciation: null,
        audio_url: null,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await exampleEndpoints.getWordDefinition('xyz');

      expect(result.data?.pronunciation).toBeNull();
      expect(result.data?.audio_url).toBeNull();
      expect(result.error).toBeNull();
    });

    test('should handle network error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network timeout'));

      const result = await exampleEndpoints.getWordDefinition('hello');

      expect(result.error).toBeTruthy();
    });

    test('should handle server error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => JSON.stringify({ error: 'Internal server error' }),
      } as Response);

      const result = await exampleEndpoints.getWordDefinition('hello');

      expect(result.error).toBeTruthy();
    });
  });

  describe('Dictionary endpoint URL construction', () => {
    test('should construct word definition endpoint with simple word', () => {
      const word = 'hello';
      const endpoint = `/define/${encodeURIComponent(word)}`;

      expect(endpoint).toBe('/define/hello');
    });

    test('should construct word definition endpoint with special characters', () => {
      const word = 'café';
      const endpoint = `/define/${encodeURIComponent(word)}`;

      expect(endpoint).toBe('/define/caf%C3%A9');
    });

    test('should construct word definition endpoint with spaces', () => {
      const word = 'ice cream';
      const endpoint = `/define/${encodeURIComponent(word)}`;

      expect(endpoint).toBe('/define/ice%20cream');
    });

    test('should construct word definition endpoint with numbers', () => {
      const word = '3D';
      const endpoint = `/define/${encodeURIComponent(word)}`;

      expect(endpoint).toBe('/define/3D');
    });

    test('should safely encode special URL characters', () => {
      const word = 'hello?world&test=1';
      const endpoint = `/define/${encodeURIComponent(word)}`;

      expect(endpoint).toBe('/define/hello%3Fworld%26test%3D1');
    });
  });
});
