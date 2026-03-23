import { storage } from "../utils/storage";

type MethodType = "GET" | "POST" | "DELETE" | "PUT";
type UnauthorizedHandler = () => Promise<void> | void;

type StoredUser = {
  token?: string;
  refreshToken?: string;
};

let unauthorizedHandler: UnauthorizedHandler | null = null;
let refreshPromise: Promise<string | null> | null = null;

export const setUnauthorizedHandler = (
  handler: UnauthorizedHandler | null,
): void => {
  unauthorizedHandler = handler;
};

const getStoredUser = async (): Promise<StoredUser | null> => {
  try {
    const userData = await storage.getItem("user");
    if (!userData) {
      return null;
    }

    return JSON.parse(userData) as StoredUser;
  } catch (error) {
    console.error("Error retrieving stored user:", error);
    return null;
  }
};

const updateStoredTokens = async (
  accessToken: string,
  refreshToken?: string,
): Promise<void> => {
  try {
    const userData = await storage.getItem("user");
    if (!userData) {
      return;
    }

    const user = JSON.parse(userData) as StoredUser;
    const updatedUser = {
      ...user,
      token: accessToken,
      refreshToken: refreshToken ?? user.refreshToken,
    };

    await storage.setItem("user", JSON.stringify(updatedUser));
  } catch (error) {
    console.error("Error updating stored tokens:", error);
  }
};

const refreshAccessToken = async (): Promise<string | null> => {
  const user = await getStoredUser();
  const refreshToken = user?.refreshToken;

  if (!refreshToken) {
    return null;
  }

  try {
    const url = `${process.env.EXPO_PUBLIC_API_URL}/auth/refresh`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${refreshToken}`,
      },
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    const newAccessToken: string | undefined = data?.tokens?.access_token;
    const newRefreshToken: string | undefined = data?.tokens?.refresh_token;

    if (!newAccessToken) {
      return null;
    }

    await updateStoredTokens(newAccessToken, newRefreshToken);
    return newAccessToken;
  } catch (error) {
    console.error("Error refreshing token:", error);
    return null;
  }
};

const getFreshAccessToken = async (): Promise<string | null> => {
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
};

/**
 * Get the stored authentication token
 */
const getAuthToken = async (): Promise<string | null> => {
  try {
    const user = await getStoredUser();
    return user?.token || null;
  } catch (error) {
    console.error("Error retrieving auth token:", error);
  }
  return null;
};

const request = async (
  method: MethodType,
  endpoint: string,
  body: BodyInit | null | undefined = null,
  tokenOverride: string | null = null,
  hasRetried = false,
): Promise<{ data: any; error: string | null }> => {
  const url = `${process.env.EXPO_PUBLIC_API_URL}${endpoint}`;

  try {
    // Get token from secure storage
    let token = tokenOverride ?? (await getAuthToken());

    if (!token) {
      token = await getFreshAccessToken();

      if (!token) {
        await unauthorizedHandler?.();
        throw new Error(`HTTP 401 - Invalid token`);
      }
    }

    const headers: HeadersInit = {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };

    const response = await fetch(url, {
      method,
      headers,
      body,
    });

    const responseText = await response.text();
    let data: any = null;

    if (responseText) {
      try {
        data = JSON.parse(responseText);
      } catch {
        data = { error: responseText };
      }
    }

    // Handle HTTP error responses
    if (!response.ok) {
      if (response.status === 401) {
        if (!hasRetried) {
          const refreshedToken = await getFreshAccessToken();

          if (refreshedToken) {
            return request(method, endpoint, body, refreshedToken, true);
          }
        }

        await unauthorizedHandler?.();
      }
      const backendError =
        data?.error || data?.message || response.statusText || "Request failed";
      throw new Error(`HTTP ${response.status} - ${backendError}`);
    }

    // // 204 No Content (common for deletes) has no body to parse
    // if (response.status === 204) {
    //   return { data: null, error: null };
    // }

    return { data: data, error: null };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : (error as string);
    console.log(`Error fetching from ${url}. ${errorMessage}`);
    // Split error message by " - " and return the last part
    const errorParts = errorMessage.split(" - ");
    const cleanError = errorParts[errorParts.length - 1];
    return {
      data: null,
      error: cleanError,
    };
  }
};

const client = {
  get: (endpoint: string) => request("GET", endpoint),
  post: (endpoint: string, body: BodyInit | null | undefined) =>
    request("POST", endpoint, body),
  delete: (endpoint: string) => request("DELETE", endpoint),
  put: (endpoint: string, body: BodyInit | null | undefined) =>
    request("PUT", endpoint, body),
};

export default client;
