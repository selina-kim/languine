import { storage } from "../utils/storage";

type MethodType = "GET" | "POST" | "DELETE" | "PUT";

/**
 * Get the stored authentication token
 */
const getAuthToken = async (): Promise<string | null> => {
  try {
    const userData = await storage.getItem("user");
    if (userData) {
      const user = JSON.parse(userData);
      return user.token || null;
    }
  } catch (error) {
    console.error("Error retrieving auth token:", error);
  }
  return null;
};

const request = async (
  method: MethodType,
  endpoint: string,
  body: BodyInit | null | undefined = null,
) => {
  const url = `${process.env.EXPO_PUBLIC_API_URL}${endpoint}`;

  // Get token from secure storage
  const token = await getAuthToken();

  try {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };

    // Add Authorization header if token exists
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      method,
      headers,
      body: body,
    });

    if (!response.ok) {
      throw new Error(
        `HTTP Error Status: ${response.status} - ${response.statusText}`,
      );
    }

    // 204 No Content (common for deletes) has no body to parse
    if (response.status === 204) {
      return { data: null, error: null };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : error;
    return {
      data: null,
      error: `Error fetching from ${url}. ${errorMessage}`,
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
