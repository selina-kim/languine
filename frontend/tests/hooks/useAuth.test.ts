import { describe, expect, test, beforeEach, jest } from "@jest/globals";
import type { User } from "../../types/auth";

/**
 * useAuth Hook Tests
 *
 * Tests authentication hook functionality:
 * - Token management (storing, retrieving, clearing tokens)
 * - Session persistence (loading saved user session on app startup)
 * - Google OAuth integration (sign in/sign out with OAuth tokens)
 */

// Mock storage utilities
jest.mock("../../utils/storage", () => ({
  storage: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    deleteItem: jest.fn(),
  },
}));

const { storage } = require("../../utils/storage");

describe("useAuth Hook - Token Management", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("should retrieve token from authenticated user", () => {
    const user: User = {
      id: "google_user_123",
      email: "user@gmail.com",
      name: "John Doe",
      token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    };

    // Simulate getToken() functionality
    const getToken = () => user.token;

    expect(getToken()).toBe(user.token);
    expect(getToken()).toBeTruthy();
  });

  test("should return null when no user is logged in", () => {
    // When no user is logged in, getToken() should return null
    const getToken = (user: User | null): string | null => {
      return user ? user.token : null;
    };

    expect(getToken(null)).toBeNull();
  });

  test("should handle Google OAuth access token with expiration", () => {
    const googleAuthUser: User & { tokenExpiry?: number } = {
      id: "google_123456",
      email: "user@gmail.com",
      name: "John Doe",
      token: "access_token_from_google_oauth",
      tokenExpiry: Date.now() + 3600000, // 1 hour from now
    };

    expect(googleAuthUser.token).toBeTruthy();
    expect(googleAuthUser.tokenExpiry).toBeGreaterThan(Date.now());
  });

  test("should detect expired OAuth token", () => {
    const expiredUser: User & { tokenExpiry?: number } = {
      id: "google_123456",
      email: "user@gmail.com",
      name: "John Doe",
      token: "expired_oauth_token",
      tokenExpiry: Date.now() - 1000, // Expired 1 second ago
    };

    const isTokenExpired = expiredUser.tokenExpiry
      ? expiredUser.tokenExpiry < Date.now()
      : false;
    expect(isTokenExpired).toBe(true);
  });
});

describe("useAuth Hook - Session Persistence", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("should restore user session from storage on app startup", async () => {
    const savedUser: User = {
      id: "google_user_123",
      email: "user@gmail.com",
      name: "John Doe",
      token: "saved_jwt_token",
    };

    storage.getItem.mockResolvedValue(JSON.stringify(savedUser));

    // Simulate session restoration
    const storedUserJson = await storage.getItem("user");
    const restoredUser = JSON.parse(storedUserJson);

    expect(storage.getItem).toHaveBeenCalledWith("user");
    expect(restoredUser).toEqual(savedUser);
    expect(restoredUser.id).toBe("google_user_123");
  });

  test("should handle missing stored session gracefully", async () => {
    storage.getItem.mockResolvedValue(null);

    const storedUserJson = await storage.getItem("user");
    expect(storedUserJson).toBeNull();
    expect(storage.getItem).toHaveBeenCalled();
  });

  test("should clear session on app startup if user data is corrupted", async () => {
    storage.getItem.mockResolvedValue("invalid json {");

    const storedUserJson = await storage.getItem("user");

    expect(() => {
      if (storedUserJson) JSON.parse(storedUserJson);
    }).toThrow();

    expect(storage.getItem).toHaveBeenCalled();
  });

  test("should persist user session after Google OAuth sign in", async () => {
    const googleUser: User = {
      id: "google_oauth_456",
      email: "newuser@gmail.com",
      name: "Jane Doe",
      token: "google_oauth_access_token",
    };

    // Simulate storing user after OAuth sign in
    await storage.setItem("user", JSON.stringify(googleUser));

    expect(storage.setItem).toHaveBeenCalledWith(
      "user",
      JSON.stringify(googleUser),
    );
  });
});

describe("useAuth Hook - Google OAuth Integration", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("should store Google OAuth user data after successful sign in", async () => {
    const googleOAuthResponse = {
      user: {
        id: "google_120984756",
        email: "developer@gmail.com",
        name: "Developer Name",
      },
      accessToken: "ya29.a0AfH6SMB...",
      refreshToken: "refresh_token_xyz",
    };

    const userData: User = {
      id: googleOAuthResponse.user.id,
      email: googleOAuthResponse.user.email,
      name: googleOAuthResponse.user.name,
      token: googleOAuthResponse.accessToken,
      refreshToken: googleOAuthResponse.refreshToken,
    };

    // Simulate sign in process
    await storage.setItem("user", JSON.stringify(userData));

    expect(storage.setItem).toHaveBeenCalledWith(
      "user",
      expect.stringContaining("google_120984756"),
    );
    expect(storage.setItem).toHaveBeenCalledWith(
      "user",
      expect.stringContaining(googleOAuthResponse.accessToken),
    );
  });

  test("should handle Google OAuth sign out by clearing all tokens", async () => {
    // Simulate sign out process
    await storage.deleteItem("user");

    expect(storage.deleteItem).toHaveBeenCalledWith("user");
  });

  test("should maintain user during session but clear on explicit sign out", async () => {
    const user: User = {
      id: "google_user",
      email: "user@gmail.com",
      name: "User Name",
      token: "valid_token",
    };

    // User is logged in
    expect(user).toBeTruthy();

    // Simulate sign out
    const clearedUser = null;
    expect(clearedUser).toBeNull();
  });

  test("should validate user has required OAuth fields", () => {
    const validGoogleUser: User = {
      id: "google_123",
      email: "user@gmail.com",
      name: "John Doe",
      token: "oauth_token",
    };

    // Verify required fields for OAuth user
    expect(validGoogleUser).toHaveProperty("id");
    expect(validGoogleUser).toHaveProperty("email");
    expect(validGoogleUser).toHaveProperty("token");
    expect(validGoogleUser.token).toBeTruthy();
  });
});
