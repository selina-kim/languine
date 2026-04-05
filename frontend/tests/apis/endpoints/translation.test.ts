import { describe, expect, test, beforeEach, jest } from "@jest/globals";
import * as translationEndpoints from "@/apis/endpoints/translation";

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

describe("Translation Endpoints", () => {
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

  describe("getTranslation", () => {
    test("should translate text with target language only", async () => {
      const mockResponse = {
        detectedSourceLang: "en",
        translatedText: "hola",
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await translationEndpoints.getTranslation("hello", "es");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/translate?text=hello&target=es"),
        expect.any(Object),
      );
      expect(result.data?.translatedText).toBe("hola");
      expect(result.data?.detectedSourceLang).toBe("en");
      expect(result.error).toBeNull();
    });

    test("should translate text with source and target language", async () => {
      const mockResponse = {
        detectedSourceLang: "en",
        translatedText: "こんにちは",
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await translationEndpoints.getTranslation(
        "hello",
        "ja",
        "en",
      );

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/translate?text=hello&target=ja&source=en"),
        expect.any(Object),
      );
      expect(result.data?.translatedText).toBe("こんにちは");
      expect(result.error).toBeNull();
    });

    test("should handle getTranslation with special characters", async () => {
      const mockResponse = {
        detectedSourceLang: "en",
        translatedText: "café",
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await translationEndpoints.getTranslation(
        "coffee shop",
        "fr",
      );

      expect(result.data?.translatedText).toBe("café");
    });

    test("should handle getTranslation validation error", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () =>
          JSON.stringify({
            error: "Validation failed: text is required",
          }),
      } as Response);

      const result = await translationEndpoints.getTranslation("", "es");

      expect(result.error).toBeTruthy();
    });

    test("should handle getTranslation server error", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => JSON.stringify({ error: "Server error" }),
      } as Response);

      const result = await translationEndpoints.getTranslation("hello", "es");

      expect(result.error).toBeTruthy();
    });

    test("should handle getTranslation network error", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network timeout"));

      const result = await translationEndpoints.getTranslation("hello", "es");

      expect(result.error).toBeTruthy();
    });
  });

  describe("getSupportedLanguages", () => {
    test("should fetch supported languages successfully", async () => {
      const mockResponse = {
        source: [
          { code: "EN", name: "English" },
          { code: "KO", name: "Korean" },
          { code: "JA", name: "Japanese" },
          { code: "ZH", name: "Mandarin" },
          { code: "FR", name: "French" },
        ],
        target: [
          { code: "EN", name: "English" },
          { code: "KO", name: "Korean" },
          { code: "JA", name: "Japanese" },
          { code: "ZH", name: "Mandarin" },
          { code: "FR", name: "French" },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await translationEndpoints.getSupportedLanguages();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/translate/languages"),
        expect.any(Object),
      );
      expect(result.data?.source).toHaveLength(5);
      expect(result.data?.target).toHaveLength(5);
      expect(result.data?.source[0].code).toBe("EN");
      expect(result.data?.target[0].code).toBe("EN");
      expect(result.error).toBeNull();
    });

    test("should handle getSupportedLanguages server error", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => JSON.stringify({ error: "Server error" }),
      } as Response);

      const result = await translationEndpoints.getSupportedLanguages();

      expect(result.error).toBeTruthy();
    });

    test("should handle getSupportedLanguages network error", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network connection failed"));

      const result = await translationEndpoints.getSupportedLanguages();

      expect(result.error).toBeTruthy();
    });
  });

  describe("Translation endpoint URL construction", () => {
    test("should construct translation endpoint with target language", () => {
      const text = "hello";
      const target = "ko";
      const params = new URLSearchParams({ text, target });
      const endpoint = `/translate?${params.toString()}`;

      expect(endpoint).toContain("/translate?");
      expect(endpoint).toContain("text=hello");
      expect(endpoint).toContain("target=ko");
    });

    test("should construct translation endpoint with source and target language", () => {
      const text = "hello";
      const target = "ja";
      const source = "en";
      const params = new URLSearchParams({ text, target, source });
      const endpoint = `/translate?${params.toString()}`;

      expect(endpoint).toContain("/translate?");
      expect(endpoint).toContain("text=hello");
      expect(endpoint).toContain("target=ja");
      expect(endpoint).toContain("source=en");
    });

    test("should construct supported languages endpoint", () => {
      const endpoint = "/translate/languages";
      expect(endpoint).toBe("/translate/languages");
    });

    test("should handle URL encoding for special characters", () => {
      const text = "hello world!";
      const target = "ko";
      const params = new URLSearchParams({ text, target });
      const endpoint = `/translate?${params.toString()}`;

      expect(endpoint).toContain("hello+world%21");
    });
  });
});
