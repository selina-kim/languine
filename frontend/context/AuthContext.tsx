import { User } from "@/types/auth";
import { useRouter, useSegments } from "expo-router";
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { storage } from "@/utils/storage";
import { setUnauthorizedHandler } from "@/apis/client";

interface AuthContextType {
  user: User | null;
  signIn: (userData: User) => Promise<void>;
  signOut: () => Promise<void>;
  getToken: () => string | null;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  signIn: async () => {},
  signOut: async () => {},
  getToken: () => null,
  isLoading: true,
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const segments = useSegments();

  const clearStoredAuth = useCallback(async () => {
    setUser(null);
    try {
      await storage.deleteItem("user");
    } catch (error) {
      console.error("Error clearing auth:", error);
    }
  }, []);

  useEffect(() => {
    // Check if user is already logged in from stored token
    const checkAuth = async () => {
      try {
        const storedUser = await storage.getItem("user");
        if (storedUser) {
          const userData = JSON.parse(storedUser);
          setUser(userData);
        }
      } catch (error) {
        console.error("Error loading stored auth:", error);
      } finally {
        setIsLoading(false);
      }
    };
    checkAuth();
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(async () => {
      await clearStoredAuth();
      router.replace("/(auth)");
    });

    return () => {
      setUnauthorizedHandler(null);
    };
  }, [clearStoredAuth, router]);

  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === "(auth)";

    // Redirect authenticated users away from auth pages to tabs
    if (user && inAuthGroup) {
      router.replace("/(tabs)");
    }
    // Redirect unauthenticated users to auth/login page
    else if (!user && !inAuthGroup) {
      router.replace("/(auth)");
    }
  }, [user, segments, isLoading, router]);

  const signIn = async (userData: User) => {
    setUser(userData);
    // Store user data securely
    try {
      await storage.setItem("user", JSON.stringify(userData));
    } catch (error) {
      console.error("Error storing auth:", error);
    }
  };

  const signOut = async () => {
    await clearStoredAuth();
    router.replace("/(auth)");
  };

  const getToken = () => {
    return user?.token || null;
  };

  return (
    <AuthContext.Provider
      value={{ user, signIn, signOut, getToken, isLoading }}
    >
      {children}
    </AuthContext.Provider>
  );
}
