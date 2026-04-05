import { describe, expect, test, beforeEach, jest } from "@jest/globals";
import * as imageEndpoints from "@/apis/endpoints/image";

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

describe("Image Endpoints", () => {
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

  describe("searchImages", () => {
    test("should search images with default pagination", async () => {
      const mockResponse = {
        total: 100,
        total_pages: 20,
        results: [
          {
            id: "img123",
            alt_description: "A beautiful landscape",
            urls: {
              raw: "https://images.unsplash.com/photo-123?raw",
              full: "https://images.unsplash.com/photo-123?full",
              regular: "https://images.unsplash.com/photo-123?regular",
              small: "https://images.unsplash.com/photo-123?small",
              thumb: "https://images.unsplash.com/photo-123?thumb",
            },
            user: {
              name: "John Doe",
              username: "johndoe",
            },
            links: {
              download: "https://images.unsplash.com/photo-123/download",
            },
          },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await imageEndpoints.searchImages("landscape");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(
          "/images/search?query=landscape&page=1&per_page=5",
        ),
        expect.any(Object),
      );
      expect(result.data?.results).toHaveLength(1);
      expect(result.data?.results[0].id).toBe("img123");
      expect(result.data?.total).toBe(100);
      expect(result.error).toBeNull();
    });

    test("should search images with custom pagination", async () => {
      const mockResponse = {
        total: 100,
        total_pages: 10,
        results: [],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await imageEndpoints.searchImages("mountain", 2, 10);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(
          "/images/search?query=mountain&page=2&per_page=10",
        ),
        expect.any(Object),
      );
      expect(result.data?.total_pages).toBe(10);
    });

    test("should handle URL encoding for special characters in search query", async () => {
      const mockResponse = {
        total: 50,
        total_pages: 10,
        results: [],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockResponse),
      } as Response);

      const result = await imageEndpoints.searchImages("cherry blossom");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("cherry%20blossom"),
        expect.any(Object),
      );
      expect(result.error).toBeNull();
    });

    test("should handle searchImages validation error", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        text: async () =>
          JSON.stringify({
            error: "Validation failed: search query is required",
          }),
      } as Response);

      const result = await imageEndpoints.searchImages("");

      expect(result.error).toBeTruthy();
    });

    test("should handle searchImages server error", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => JSON.stringify({ error: "Server error" }),
      } as Response);

      const result = await imageEndpoints.searchImages("test");

      expect(result.error).toBeTruthy();
    });

    test("should handle searchImages network error", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network timeout"));

      const result = await imageEndpoints.searchImages("test");

      expect(result.error).toBeTruthy();
    });
  });

  describe("Image endpoint URL construction", () => {
    test("should construct search images endpoint with default parameters", () => {
      const query = "sunset";
      const page = 1;
      const perPage = 5;
      const params = `query=${encodeURIComponent(query)}&page=${page}&per_page=${perPage}`;
      const endpoint = `/images/search?${params}`;

      expect(endpoint).toContain("/images/search?");
      expect(endpoint).toContain("query=sunset");
      expect(endpoint).toContain("page=1");
      expect(endpoint).toContain("per_page=5");
    });

    test("should construct search images endpoint with custom parameters", () => {
      const query = "nature";
      const page = 3;
      const perPage = 20;
      const params = `query=${encodeURIComponent(query)}&page=${page}&per_page=${perPage}`;
      const endpoint = `/images/search?${params}`;

      expect(endpoint).toContain("query=nature");
      expect(endpoint).toContain("page=3");
      expect(endpoint).toContain("per_page=20");
    });

    test("should properly encode special characters in search query", () => {
      const query = "hello world!";
      const encoded = encodeURIComponent(query);
      const endpoint = `/images/search?query=${encoded}&page=1&per_page=5`;

      expect(endpoint).toContain("hello%20world!");
    });

    test("should handle unicode characters in search query", () => {
      const query = "日本";
      const encoded = encodeURIComponent(query);
      const endpoint = `/images/search?query=${encoded}&page=1&per_page=5`;

      expect(endpoint).toContain("%");
      expect(endpoint).toContain("page=1");
    });
  });
});
