/**
 * Authentication types
 */

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  token: string; // Backend JWT token
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
}
