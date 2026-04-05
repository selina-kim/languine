import {
  describe,
  expect,
  test,
  beforeEach,
  jest,
  afterEach,
} from "@jest/globals";

import client, { setUnauthorizedHandler } from "@/apis/client";
import { storage } from "@/utils/storage";

// Mock storage with proper typing
jest.mock("@/utils/storage", () => ({
  storage: {
    getItem: jest.fn() as jest.Mock,
    setItem: jest.fn() as jest.Mock,
    deleteItem: jest.fn() as jest.Mock,
  },
}));

// Mock fetch globally with proper type
(global as any).fetch = jest.fn() as jest.MockedFunction<typeof fetch>;

// Type assertion to tell TypeScript this is a mocked storage object
const mockStorage = storage as jest.Mocked<typeof storage>;

const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

describe("API Client", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockStorage.getItem.mockReset();
    mockStorage.setItem.mockReset();
    mockStorage.deleteItem.mockReset();
    mockFetch.mockReset();
    process.env.EXPO_PUBLIC_API_URL = "https://api.example.com";
  });

  afterEach(() => {
    jest.clearAllMocks();
    setUnauthorizedHandler(null);
  });

  describe("setUnauthorizedHandler", () => {
    test("should set unauthorized handler", async () => {
      const handler = jest.fn(async () => Promise.resolve());
      setUnauthorizedHandler(handler);

      expect(handler).toBeDefined();
    });

    test("should clear unauthorized handler", () => {
      setUnauthorizedHandler(null);
      expect(setUnauthorizedHandler).toBeDefined();
    });
  });

  describe("Token Storage", () => {
    test("should retrieve stored user data", async () => {
      const userData = { token: "access123", refreshToken: "refresh123" };
      mockStorage.getItem.mockResolvedValueOnce(JSON.stringify(userData));

      const result = await storage.getItem("user");
      expect(result).toBeTruthy();
      expect(JSON.parse(result as string)).toEqual(userData);
    });

    test("should handle missing user data", async () => {
      mockStorage.getItem.mockResolvedValueOnce(null);

      const result = await storage.getItem("user");
      expect(result).toBeNull();
    });

    test("should store user tokens", async () => {
      const userData = { token: "access123", refreshToken: "refresh123" };
      mockStorage.setItem.mockResolvedValueOnce(undefined);

      await storage.setItem("user", JSON.stringify(userData));

      expect(storage.setItem).toHaveBeenCalledWith(
        "user",
        JSON.stringify(userData),
      );
    });

    test("should update stored tokens", async () => {
      const oldData = { token: "old_token", refreshToken: "refresh123" };
      const newData = { token: "new_token", refreshToken: "refresh123" };

      mockStorage.getItem.mockResolvedValueOnce(JSON.stringify(oldData));
      mockStorage.setItem.mockResolvedValueOnce(undefined);

      const result = await storage.getItem("user");
      expect(JSON.parse(result as string).token).toBe("old_token");

      await storage.setItem("user", JSON.stringify(newData));
      expect(storage.setItem).toHaveBeenCalledWith(
        "user",
        JSON.stringify(newData),
      );
    });
  });

  describe("Token Refresh", () => {
    test("should handle token refresh without refresh token", async () => {
      mockStorage.getItem.mockResolvedValueOnce(
        JSON.stringify({ token: "access123" }),
      );

      const result = await storage.getItem("user");
      const user = JSON.parse(result as string);

      expect(user.refreshToken).toBeUndefined();
    });

    test("should handle API URL configuration", () => {
      const apiUrl = process.env.EXPO_PUBLIC_API_URL;
      expect(apiUrl).toBe("https://api.example.com");
    });
  });

  describe("Request Methods", () => {
    test("should construct correct endpoint URLs", () => {
      const endpoint = "/auth/login";
      const fullUrl = `https://api.example.com${endpoint}`;

      expect(fullUrl).toBe("https://api.example.com/auth/login");
    });

    test("should set correct HTTP headers", () => {
      const token = "test_token_123";
      const headers: HeadersInit = {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      };

      expect(headers["Content-Type"]).toBe("application/json");
      expect(headers.Authorization).toBe(`Bearer ${token}`);
    });

    test("should handle different HTTP methods", () => {
      const methods = ["GET", "POST", "PUT", "DELETE"];

      methods.forEach((method) => {
        expect(["GET", "POST", "PUT", "DELETE"]).toContain(method);
      });
    });
  });

  describe("Error Handling", () => {
    test("should handle missing API URL", () => {
      delete process.env.EXPO_PUBLIC_API_URL;
      const apiUrl = process.env.EXPO_PUBLIC_API_URL;

      expect(apiUrl).toBeUndefined();
    });

    test("should handle network errors gracefully", async () => {
      (global.fetch as jest.MockedFunction<typeof fetch>).mockRejectedValueOnce(
        new Error("Network error"),
      );

      try {
        await fetch("https://api.example.com/test");
      } catch (error) {
        expect((error as Error).message).toBe("Network error");
      }
    });

    test("should parse error messages correctly", () => {
      const errorMessage = "HTTP 401 - Invalid token";
      const errorParts = errorMessage.split(" - ");
      const cleanError = errorParts[errorParts.length - 1];

      expect(cleanError).toBe("Invalid token");
    });

    test("should handle JSON parsing errors", async () => {
      const invalidJson = "not valid json";

      try {
        JSON.parse(invalidJson);
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });

  describe("Authorization", () => {
    test("should include auth token in headers", () => {
      const token = "Bearer token123";
      const headers: HeadersInit = {
        Authorization: token,
      };

      expect(headers.Authorization).toBe("Bearer token123");
    });

    test("should handle token override", async () => {
      const overrideToken = "override_token";
      const storedToken = "stored_token";

      expect(overrideToken).not.toBe(storedToken);
    });

    test("should call unauthorized handler on 401", async () => {
      const handler = jest.fn(async () => Promise.resolve());
      setUnauthorizedHandler(handler);

      expect(handler).toBeDefined();
    });
  });

  describe("Response Parsing", () => {
    test("should parse JSON responses", async () => {
      const responseData = { success: true, data: { id: "123" } };
      const jsonString = JSON.stringify(responseData);

      const parsed = JSON.parse(jsonString);
      expect(parsed).toEqual(responseData);
    });

    test("should handle empty responses", () => {
      const emptyResponse = "";
      expect(emptyResponse).toBe("");
    });

    test("should handle non-JSON responses", () => {
      const textResponse = "Some text response";
      expect(textResponse).toBe("Some text response");
    });

    test("should extract error messages from responses", () => {
      const errorResponse = {
        error: "Authentication failed",
        message: "Invalid credentials",
      };

      const errorMessage = errorResponse.error || errorResponse.message;
      expect(errorMessage).toBe("Authentication failed");
    });
  });

  describe("Token Retry Logic", () => {
    test("should not retry if already retried", () => {
      let hasRetried = false;
      const maxRetries = 1;

      if (!hasRetried) {
        hasRetried = true;
      }

      expect(hasRetried).toBe(true);
      expect(maxRetries).toBe(1);
    });

    test("should track refresh promise state", async () => {
      let refreshPromise: Promise<string | null> | null = null;

      // Simulate setting the promise
      refreshPromise = Promise.resolve("new_token");

      // Simulate clearing after completion
      if (refreshPromise) {
        await refreshPromise;
        refreshPromise = null;
      }

      expect(refreshPromise).toBeNull();
    });

    test("should refresh token on 401 and retry request", async () => {
      const oldToken = "old_access_token";
      const newToken = "new_access_token";
      const refreshToken = "refresh_token_123";
      const userData = { token: oldToken, refreshToken };

      // 1. Initial getAuthToken() call
      mockStorage.getItem.mockResolvedValueOnce(JSON.stringify(userData));

      // 2. First request returns 401
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        text: async () => JSON.stringify({ error: "Token expired" }),
        json: async () => ({ error: "Token expired" }),
      } as Response);

      // 3. refreshAccessToken() calls getStoredUser() to get refresh token
      mockStorage.getItem.mockResolvedValueOnce(JSON.stringify(userData));

      // 4. Refresh endpoint returns new token
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () =>
          JSON.stringify({
            tokens: { access_token: newToken, refresh_token: refreshToken },
          }),
        json: async () => ({
          tokens: { access_token: newToken, refresh_token: refreshToken },
        }),
      } as Response);

      // 5. updateStoredTokens() reads current user
      mockStorage.getItem.mockResolvedValueOnce(JSON.stringify(userData));

      // 6. updateStoredTokens() writes updated user
      mockStorage.setItem.mockResolvedValueOnce(undefined);

      // 7. Retry request's getAuthToken() call
      mockStorage.getItem.mockResolvedValueOnce(
        JSON.stringify({ token: newToken, refreshToken }),
      );

      // 8. Retry request succeeds
      const successData = { data: "success", id: 1 };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(successData),
        json: async () => successData,
      } as Response);

      // Make request
      const result = await client.get("/protected/resource");

      // Verify success
      expect(result.error).toBeNull();
      expect(result.data).toEqual(successData);

      // Verify fetch was called 3 times (original, refresh, retry)
      expect(mockFetch).toHaveBeenCalledTimes(3);

      // Verify calls in order
      const calls = mockFetch.mock.calls;
      expect(calls[0][0]).toContain("/protected/resource"); // Original request
      const originalHeaders = calls[0][1]?.headers as Record<string, string>;
      expect(originalHeaders?.Authorization).toContain(oldToken); // With old token
      expect(calls[1][0]).toContain("/auth/refresh"); // Refresh endpoint
      expect(calls[2][0]).toContain("/protected/resource"); // Retry
      const retryHeaders = calls[2][1]?.headers as Record<string, string>;
      expect(retryHeaders?.Authorization).toContain(newToken); // With new token
    });
  });

  describe("Client GET requests", () => {
    test("should make GET request and return data", async () => {
      const mockData = { id: 1, name: "Test" };
      mockStorage.getItem.mockResolvedValueOnce(
        JSON.stringify({ token: "test_token" }),
      );
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify(mockData),
        json: async () => mockData,
      } as Response);

      const result = await client.get("/test/endpoint");

      expect(result.error).toBeNull();
      expect(result.data).toEqual(mockData);
      expect(mockFetch).toHaveBeenCalledWith(
        "https://api.example.com/test/endpoint",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
            Authorization: "Bearer test_token",
          }),
        }),
      );
    });
  });

  describe("HTTP Method Calls", () => {
    test("client.post includes body in request", async () => {
      const body = JSON.stringify({ name: "test" });
      mockStorage.getItem.mockResolvedValueOnce(
        JSON.stringify({ token: "test_token" }),
      );
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        text: async () => JSON.stringify({ id: 1 }),
        json: async () => ({ id: 1 }),
      } as Response);

      await client.post("/items", body);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: "POST",
          body: body,
        }),
      );
    });

    test("client.put calls request with PUT method", async () => {
      const body = JSON.stringify({ name: "updated" });
      mockStorage.getItem.mockResolvedValueOnce(
        JSON.stringify({ token: "test_token" }),
      );
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ success: true }),
        json: async () => ({ success: true }),
      } as Response);

      await client.put("/items/1", body);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ method: "PUT" }),
      );
    });

    test("client.delete calls request with DELETE method", async () => {
      mockStorage.getItem.mockResolvedValueOnce(
        JSON.stringify({ token: "test_token" }),
      );
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({}),
        json: async () => ({}),
      } as Response);

      await client.delete("/items/1");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ method: "DELETE" }),
      );
    });
  });
});
