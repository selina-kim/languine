import { useRouter, useSegments } from "expo-router";
import React, { createContext, useContext, useEffect, useState } from "react";

interface AuthContextType {
  user: any | null;
  signIn: (userData: any) => void;
  signOut: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  signIn: () => {},
  signOut: () => {},
  isLoading: true,
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const segments = useSegments();

  useEffect(() => {
    // Check if user is already logged in (e.g., from stored token)
    // For now, we'll just set loading to false
    // TODO: Check AsyncStorage or SecureStore for stored token
    const checkAuth = async () => {
      // const token = await SecureStore.getItemAsync('userToken');
      // if (token) {
      //   // Validate token with backend and set user
      //   setUser({ token });
      // }
      setIsLoading(false);
    };
    checkAuth();
  }, []);

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

  const signIn = (userData: any) => {
    setUser(userData);
  };

  const signOut = () => {
    setUser(null);
    // TODO: Clear stored token
    // await SecureStore.deleteItemAsync('userToken');
    router.replace("/(auth)");
  };

  return (
    <AuthContext.Provider value={{ user, signIn, signOut, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}
