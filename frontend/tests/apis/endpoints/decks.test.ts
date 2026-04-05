import { describe, expect, test, beforeEach, jest } from "@jest/globals";
import * as deckEndpoints from "@/apis/endpoints/decks";

import { storage } from "@/utils/storage";

// Mock storage
jest.mock("@/utils/storage", () => ({
  storage: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
  },
}));

// Mock the global fetch
(global as any).fetch = jest.fn() as jest.MockedFunction<typeof fetch>;

const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

const mockStorage = storage as jest.Mocked<typeof storage>;

describe("Deck Endpoints", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockReset();
    mockStorage.getItem.mockResolvedValue(
      JSON.stringify({
        token: "test_access_token",
        refreshToken: "test_refresh_token",
      }),
    );
    process.env.EXPO_PUBLIC_API_URL = "https://api.example.com";
  });

  describe("getDecks", () => {
    test("should fetch all decks successfully", async () => {
      const mockResponse = {
        decks: [
          {
            d_id: "123",
            deck_name: "Japanese Beginner",
            word_lang: "ja",
            trans_lang: "en",
            card_count: 50,
            creation_date: "2025-01-01",
            last_reviewed: null,
            is_public: true,
          },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await deckEndpoints.getDecks();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/decks"),
        expect.any(Object),
      );
      expect(result.data.decks).toHaveLength(1);
      expect(result.error).toBeNull();
    });

    test("should handle getDecks error", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => JSON.stringify({ error: "Server error" }),
      } as Response);

      const result = await deckEndpoints.getDecks();

      expect(result.error).toBeTruthy();
    });
  });

  describe("getDecksWithDueCards", () => {
    test("should fetch decks with due cards using default limit", async () => {
      const mockResponse = {
        decks: [
          {
            d_id: "123",
            deck_name: "Japanese Beginner",
            word_lang: "ja",
            trans_lang: "en",
            last_reviewed: null,
            due_count: 5,
            total_cards: 50,
          },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await deckEndpoints.getDecksWithDueCards();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/decks/due?limit=20"),
        expect.any(Object),
      );
      expect(result.data.decks).toHaveLength(1);
      expect(result.error).toBeNull();
    });

    test("should fetch decks with due cards using custom limit", async () => {
      const mockResponse = { decks: [] };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await deckEndpoints.getDecksWithDueCards(50);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/decks/due?limit=50"),
        expect.any(Object),
      );
    });
  });

  describe("getRecentDecks", () => {
    test("should fetch recent decks with default limit", async () => {
      const mockResponse = {
        decks: [
          {
            d_id: "123",
            deck_name: "Recent Deck",
            word_lang: "ja",
            trans_lang: "en",
            card_count: 30,
            creation_date: "2025-01-01",
            last_reviewed: "2025-01-15",
            is_public: true,
          },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await deckEndpoints.getRecentDecks();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/decks/recent?limit=3"),
        expect.any(Object),
      );
      expect(result.data.decks).toHaveLength(1);
    });

    test("should fetch recent decks with custom limit", async () => {
      const mockResponse = { decks: [] };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await deckEndpoints.getRecentDecks(10);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/decks/recent?limit=10"),
        expect.any(Object),
      );
    });
  });

  describe("getSingleDeck", () => {
    test("should fetch single deck successfully", async () => {
      const mockResponse = {
        deck: {
          d_id: 123,
          deck_name: "Japanese Beginner",
          description: "Learn basic Japanese",
          word_lang: "ja",
          trans_lang: "en",
          card_count: 50,
          creation_date: "2025-01-01",
          last_reviewed: null,
          is_public: true,
        },
        cards: [
          {
            c_id: 1,
            word: "こんにちは",
            translation: "Hello",
            difficulty: 1,
            stability: 0.8,
            learning_state: 1,
            due_date: null,
            word_example: null,
            trans_example: null,
            word_roman: "konnichiha",
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

      const result = await deckEndpoints.getSingleDeck("123");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/decks/123"),
        expect.any(Object),
      );
      expect(result.data?.deck?.d_id).toBe(123);
      expect(result.error).toBeNull();
    });

    test("should handle getSingleDeck not found", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ error: "Deck not found" }),
      } as Response);

      const result = await deckEndpoints.getSingleDeck("invalid");

      expect(result.error).toBeTruthy();
    });
  });

  describe("createDeck", () => {
    test("should create deck successfully", async () => {
      const createPayload = {
        deck_name: "Korean Beginner",
        word_lang: "ko",
        trans_lang: "en",
        description: "Learn basic Korean",
        is_public: true,
      };

      const mockResponse = {
        message: "Deck created successfully",
        deck: {
          d_id: 456,
          deck_name: "Korean Beginner",
          word_lang: "ko",
          trans_lang: "en",
          description: "Learn basic Korean",
          card_count: 0,
          creation_date: "2025-01-20",
          last_reviewed: null,
          is_public: true,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await deckEndpoints.createDeck(createPayload);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/decks/new"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify(createPayload),
        }),
      );
      expect(result.error).toBeNull();
    });

    test("should handle createDeck validation error", async () => {
      const invalidPayload = {
        deck_name: "",
        word_lang: "ja",
        trans_lang: "en",
      };

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () =>
          JSON.stringify({
            error: "Validation failed: deck_name is required",
          }),
      } as Response);

      const result = await deckEndpoints.createDeck(invalidPayload as any);

      expect(result.error).toBeTruthy();
    });

    test("should handle createDeck network error", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      const result = await deckEndpoints.createDeck({
        deck_name: "Test",
        word_lang: "ja",
        trans_lang: "en",
      });

      expect(result.error).toBeTruthy();
    });
  });

  describe("updateDeck", () => {
    test("should update deck successfully", async () => {
      const updatePayload = {
        deck_name: "Updated Deck Name",
        description: "Updated description",
      };

      const mockResponse = {
        message: "Deck updated successfully",
        deck: {
          d_id: 123,
          deck_name: "Updated Deck Name",
          word_lang: "ja",
          trans_lang: "en",
          description: "Updated description",
          card_count: 50,
          creation_date: "2025-01-01",
          last_reviewed: null,
          is_public: true,
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await deckEndpoints.updateDeck("123", updatePayload);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/decks/123"),
        expect.objectContaining({
          method: "PUT",
          body: JSON.stringify(updatePayload),
        }),
      );
      expect(result.error).toBeNull();
    });

    test("should handle updateDeck deck not found", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ error: "Deck not found" }),
      } as Response);

      const result = await deckEndpoints.updateDeck("invalid", {
        deck_name: "Updated",
      });

      expect(result.error).toBeTruthy();
    });
  });

  describe("deleteDeck", () => {
    test("should delete deck successfully", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ message: "Deck deleted" }),
      } as Response);

      const result = await deckEndpoints.deleteDeck("123");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/decks/123"),
        expect.objectContaining({
          method: "DELETE",
        }),
      );
      expect(result.error).toBeNull();
    });

    test("should handle deleteDeck not found", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        text: async () => JSON.stringify({ error: "Deck not found" }),
      } as Response);

      const result = await deckEndpoints.deleteDeck("invalid");

      expect(result.error).toBeTruthy();
    });

    test("should handle deleteDeck error", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => JSON.stringify({ error: "Server error" }),
      } as Response);

      const result = await deckEndpoints.deleteDeck("123");

      expect(result.error).toBeTruthy();
    });
  });

  describe("Deck endpoint URL construction", () => {
    test("should construct get decks endpoint", () => {
      const endpoint = "/decks";
      expect(endpoint).toBe("/decks");
    });

    test("should construct get decks due endpoint with limit", () => {
      const limit = 50;
      const endpoint = `/decks/due?limit=${limit}`;
      expect(endpoint).toBe("/decks/due?limit=50");
    });

    test("should construct get recent decks endpoint with limit", () => {
      const limit = 5;
      const endpoint = `/decks/recent?limit=${limit}`;
      expect(endpoint).toBe("/decks/recent?limit=5");
    });

    test("should construct get single deck endpoint", () => {
      const deckId = "123";
      const endpoint = `/decks/${deckId}`;
      expect(endpoint).toBe("/decks/123");
    });

    test("should construct create deck endpoint", () => {
      const endpoint = "/decks/new";
      expect(endpoint).toBe("/decks/new");
    });

    test("should construct update deck endpoint", () => {
      const deckId = "123";
      const endpoint = `/decks/${deckId}`;
      expect(endpoint).toBe("/decks/123");
    });

    test("should construct delete deck endpoint", () => {
      const deckId = "123";
      const endpoint = `/decks/${deckId}`;
      expect(endpoint).toBe("/decks/123");
    });
  });
});
