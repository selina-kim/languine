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
): Promise<{ data: any; error: string | null }> => {
  const url = `${process.env.EXPO_PUBLIC_API_URL}${endpoint}`;

  try {
    // Get token from secure storage
    const token = await getAuthToken();

    if (!token) {
      throw new Error(`HTTP 500 - Internal Server Error. User token not found`);
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

    console.log("got response");
    const data = await response.json();
    console.log("parsed response");

    // Handle HTTP error responses
    if (!response.ok) {
      throw new Error(`HTTP ${response.status} - ${data.error}`);
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
