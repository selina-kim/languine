import { User } from "@/types/auth";

/**
 * Authentication API endpoints
 */

interface GoogleAuthResponse {
  message: string;
  user: {
    u_id: string;
    email: string;
    display_name: string;
    timezone: string;
    google_id: string;
  };
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: string;
  };
}

/**
 * Exchange Google OAuth tokens for your backend JWT token
 */
export const exchangeGoogleToken = async (
  accessToken: string,
  idToken: string,
): Promise<{ token: string; user: User }> => {
  const url = `${process.env.EXPO_PUBLIC_API_URL}/auth/google`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      id_token: idToken,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.error || `Authentication failed: ${response.status}`,
    );
  }

  const data: GoogleAuthResponse = await response.json();

  // Map backend user fields to frontend User type
  return {
    token: data.tokens.access_token,
    user: {
      id: data.user.u_id,
      email: data.user.email,
      name: data.user.display_name,
      token: data.tokens.access_token,
      refreshToken: data.tokens.refresh_token,
    },
  };
};

/**
 * Validate/refresh the backend token
 */
export const refreshToken = async (
  token: string,
): Promise<{ token: string }> => {
  const url = `${process.env.EXPO_PUBLIC_API_URL}/auth/refresh`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Token refresh failed");
  }

  return response.json();
};
