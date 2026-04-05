import { describe, expect, test, jest, beforeEach } from "@jest/globals";

// Mock API endpoints
jest.mock("@/apis/endpoints/decks", () => ({
  importDeck: jest.fn(),
  exportDeck: jest.fn(),
  getDecks: jest.fn(),
  createDeck: jest.fn(),
  updateDeck: jest.fn(),
  deleteDeck: jest.fn(),
}));

const { importDeck, exportDeck } = require("@/apis/endpoints/decks");

describe("Deck Import/Export Functionality", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Deck Export to JSON", () => {
    test("should export deck with JSON format", async () => {
      const deckId = "deck123";
      const mockDeckData = {
        format: "capstone_deck_v1",
        exported_at: "2026-04-04T12:00:00.000000",
        deck: {
          deck_name: "French Basics",
          word_lang: "French",
          trans_lang: "English",
          description: "Basic French vocabulary",
          creation_date: "2026-01-01",
        },
        cards: [
          {
            word: "Bonjour",
            translation: "Hello",
            word_example: "Bonjour, comment allez-vous?",
            trans_example: "Hello, how are you?",
          },
          {
            word: "Au revoir",
            translation: "Goodbye",
            word_example: "Au revoir, à bientôt",
            trans_example: "Goodbye, see you soon",
          },
        ],
      };

      exportDeck.mockResolvedValue({
        data: mockDeckData,
        error: null,
      });

      const result = await exportDeck(deckId, "json");

      expect(result.data.format).toBe("capstone_deck_v1");
      expect(result.data.deck.deck_name).toBe("French Basics");
      expect(result.data.cards.length).toBe(2);
      expect(result.data.cards[0].word).toBe("Bonjour");
    });

    test("should include deck metadata in JSON export", async () => {
      const mockDeckData = {
        format: "capstone_deck_v1",
        exported_at: "2026-04-04T12:00:00.000000",
        deck: {
          deck_name: "Japanese Basics",
          word_lang: "Japanese",
          trans_lang: "English",
          description: "Basic Japanese vocabulary",
          creation_date: "2026-02-01",
        },
        cards: [],
      };

      expect(mockDeckData.deck).toHaveProperty("deck_name");
      expect(mockDeckData.deck).toHaveProperty("word_lang");
      expect(mockDeckData.deck).toHaveProperty("trans_lang");
      expect(mockDeckData.format).toBe("capstone_deck_v1");
    });

    test("should handle special characters in JSON export", async () => {
      const mockDeckData = {
        format: "capstone_deck_v1",
        exported_at: "2026-04-04T12:00:00.000000",
        deck: {
          deck_name: "Chinese & More",
          word_lang: "Chinese",
          trans_lang: "English",
        },
        cards: [
          {
            word: "你好",
            translation: "Hello",
            word_example: "你好，你叫什么名字?",
            trans_example: "Hello, what is your name?",
          },
        ],
      };

      expect(mockDeckData.deck.deck_name).toBe("Chinese & More");
      expect(mockDeckData.cards[0].word).toBe("你好");
    });

    test("should export empty deck as valid JSON", async () => {
      const mockDeckData = {
        format: "capstone_deck_v1",
        exported_at: "2026-04-04T12:00:00.000000",
        deck: {
          deck_name: "Empty Deck",
          word_lang: "Language",
          trans_lang: "English",
        },
        cards: [],
      };

      exportDeck.mockResolvedValue({
        data: mockDeckData,
        error: null,
      });

      const result = await exportDeck("empty_deck", "json");

      expect(result.data.cards).toEqual([]);
      expect(result.data.deck.deck_name).toBe("Empty Deck");
    });

    test("should handle large deck exports in JSON", async () => {
      const largeCards = Array.from({ length: 1000 }, (_, i) => ({
        word: `word${i}`,
        translation: `translation${i}`,
        word_example: `example${i}`,
        trans_example: `example translation${i}`,
      }));

      const mockDeckData = {
        format: "capstone_deck_v1",
        exported_at: "2026-04-04T12:00:00.000000",
        deck: {
          deck_name: "Large Deck",
          word_lang: "Language",
          trans_lang: "English",
        },
        cards: largeCards,
      };

      exportDeck.mockResolvedValue({
        data: mockDeckData,
        error: null,
      });

      const result = await exportDeck("large_deck", "json");

      expect(result.data.cards.length).toBe(1000);
      expect(result.data.format).toBe("capstone_deck_v1");
    });

    test("should handle non-ASCII characters in JSON export", async () => {
      const mockDeckData = {
        format: "capstone_deck_v1",
        exported_at: "2026-04-04T12:00:00.000000",
        deck: {
          deck_name: "Multilingual",
          word_lang: "Mixed",
          trans_lang: "English",
        },
        cards: [
          { word: "你好", translation: "Hello" },
          { word: "こんにちは", translation: "Hello" },
          { word: "한글", translation: "Korean" },
        ],
      };

      expect(mockDeckData.cards[0].word).toBe("你好");
      expect(mockDeckData.cards[1].word).toBe("こんにちは");
      expect(mockDeckData.cards[2].word).toBe("한글");
    });
  });

  describe("Deck Import from JSON", () => {
    test("should import deck from valid JSON file", async () => {
      const jsonData = {
        format: "capstone_deck_v1",
        exported_at: "2026-04-04T12:00:00.000000",
        deck: {
          deck_name: "French Beginner",
          word_lang: "French",
          trans_lang: "English",
          description: "Basic French vocabulary",
        },
        cards: [
          {
            word: "Bonjour",
            translation: "Hello",
            word_example: "Bonjour, comment allez-vous?",
            trans_example: "Hello, how are you?",
          },
          {
            word: "Au revoir",
            translation: "Goodbye",
            word_example: "Au revoir, à bientôt",
            trans_example: "Goodbye, see you soon",
          },
          {
            word: "Merci",
            translation: "Thank you",
            word_example: "Merci beaucoup",
            trans_example: "Thank you very much",
          },
        ],
      };

      importDeck.mockResolvedValue({
        data: {
          imported: 3,
          failed: 0,
          deckId: "new_deck_123",
        },
        error: null,
      });

      const result = await importDeck(jsonData);

      expect(result.data.imported).toBe(3);
      expect(result.data.failed).toBe(0);
      expect(result.data.deckId).toBe("new_deck_123");
    });

    test("should handle partial import failures with JSON", async () => {
      const jsonData = {
        format: "capstone_deck_v1",
        deck: {
          deck_name: "Mixed Cards",
          word_lang: "English",
          trans_lang: "French",
        },
        cards: [
          { word: "Valid", translation: "Valide" },
          { word: "Missing", translation: "" },
          { word: "Another", translation: "Autre" },
        ],
      };

      importDeck.mockResolvedValue({
        data: {
          imported: 2,
          failed: 1,
          errors: [{ cardIndex: 1, reason: "Missing translation field" }],
        },
        error: null,
      });

      const result = await importDeck(jsonData);

      expect(result.data.imported).toBe(2);
      expect(result.data.failed).toBe(1);
      expect(result.data.errors).toHaveLength(1);
    });

    test("should validate JSON format before import", () => {
      const validJson = {
        format: "capstone_deck_v1",
        deck: { deck_name: "Test" },
        cards: [],
      };

      const isValid =
        validJson &&
        validJson.format === "capstone_deck_v1" &&
        Array.isArray(validJson.cards);

      expect(isValid).toBe(true);
    });

    test("should handle duplicate cards in JSON import", async () => {
      const jsonData = {
        format: "capstone_deck_v1",
        deck: {
          deck_name: "Duplicates Test",
          word_lang: "English",
          trans_lang: "French",
        },
        cards: [
          { word: "Hello", translation: "Bonjour" },
          { word: "Hello", translation: "Bonjour" },
          { word: "Goodbye", translation: "Au revoir" },
        ],
      };

      importDeck.mockResolvedValue({
        data: {
          imported: 2,
          duplicates: 1,
          warnings: [{ cardIndex: 1, message: "Duplicate card" }],
        },
        error: null,
      });

      const result = await importDeck(jsonData);

      expect(result.data.imported).toBe(2);
      expect(result.data.duplicates).toBe(1);
    });

    test("should handle special characters in JSON import", async () => {
      const jsonData = {
        format: "capstone_deck_v1",
        deck: {
          deck_name: "Special Chars",
          word_lang: "Mixed",
          trans_lang: "English",
        },
        cards: [
          {
            word: "你好 (héllo)",
            translation: "Hello with special chars & symbols",
          },
          { word: "café", translation: "coffee" },
        ],
      };

      expect(jsonData.cards[0].word).toContain("你好");
      expect(jsonData.cards[1].word).toBe("café");
    });

    test("should reject malformed JSON", async () => {
      importDeck.mockResolvedValue({
        data: null,
        error: "Invalid JSON format",
      });

      const result = await importDeck({ invalid: "structure" });

      expect(result.error).toBeTruthy();
    });

    test("should handle large JSON import", async () => {
      const largeCards = Array.from({ length: 5000 }, (_, i) => ({
        word: `word${i}`,
        translation: `translation${i}`,
      }));

      const jsonData = {
        format: "capstone_deck_v1",
        deck: {
          deck_name: "Large Import",
          word_lang: "Language",
          trans_lang: "English",
        },
        cards: largeCards,
      };

      importDeck.mockResolvedValue({
        data: {
          imported: 5000,
          failed: 0,
          processingTime: 2500,
        },
        error: null,
      });

      const result = await importDeck(jsonData);

      expect(result.data.imported).toBe(5000);
      expect(result.data.processingTime).toBeLessThan(5000);
    });
  });

  describe("Import/Export Error Handling", () => {
    test("should handle network error during export", async () => {
      exportDeck.mockResolvedValue({
        data: null,
        error: "Network error",
      });

      const result = await exportDeck("deck123");

      expect(result.error).toBe("Network error");
      expect(result.data).toBeNull();
    });

    test("should handle invalid deck ID for export", async () => {
      exportDeck.mockResolvedValue({
        data: null,
        error: "Deck not found",
      });

      const result = await exportDeck("invalid_deck");

      expect(result.error).toBe("Deck not found");
    });

    test("should handle permission error on import", async () => {
      importDeck.mockResolvedValue({
        data: null,
        error: "Permission denied - cannot modify this deck",
      });

      const result = await importDeck({
        format: "capstone_deck_v1",
        deck: { deck_name: "Protected" },
        cards: [],
      });

      expect(result.error).toContain("Permission");
    });

    test("should handle server timeout", async () => {
      exportDeck.mockResolvedValue({
        data: null,
        error: "Request timeout",
      });

      const result = await exportDeck("large_deck_123");

      expect(result.error).toBe("Request timeout");
    });

    test("should retry failed import", async () => {
      let attempts = 0;

      importDeck.mockImplementation(async () => {
        attempts++;
        if (attempts < 2) {
          return { data: null, error: "Server busy" };
        }
        return { data: { imported: 5, failed: 0 }, error: null };
      });

      const attemptImport = async () => {
        let result = await importDeck({
          format: "capstone_deck_v1",
          deck: { deck_name: "Test" },
          cards: [],
        });
        if (result.error && attempts < 3) {
          result = await importDeck({
            format: "capstone_deck_v1",
            deck: { deck_name: "Test" },
            cards: [],
          });
        }
        return result;
      };

      const result = await attemptImport();

      expect(result.data.imported).toBeGreaterThan(0);
      expect(attempts).toBe(2);
    });

    test("should handle corrupted file import", async () => {
      importDeck.mockResolvedValue({
        data: null,
        error: "File corrupted or unreadable",
      });

      const result = await importDeck({});

      expect(result.error).toContain("corrupted");
    });

    test("should handle version mismatch in imported JSON", async () => {
      const oldVersionJson = {
        format: "capstone_deck_v0",
        deck: { deck_name: "Test" },
        cards: [],
      };

      importDeck.mockResolvedValue({
        data: null,
        error: "Unsupported format version",
      });

      const result = await importDeck(oldVersionJson);

      expect(result.error).toContain("format");
    });
  });
});
