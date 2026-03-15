import { COLORS } from "@/constants/colors";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { Arimo_400Regular, Arimo_700Bold } from "@expo-google-fonts/arimo";
import { Commissioner_700Bold } from "@expo-google-fonts/commissioner";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import { ActivityIndicator, View } from "react-native";

function RootLayoutNav() {
  const { isLoading } = useAuth();

  // Show loading screen while checking auth
  if (isLoading) {
    return (
      <View
        style={{
          flex: 1,
          justifyContent: "center",
          alignItems: "center",
          backgroundColor: COLORS.background.primary,
        }}
      >
        <ActivityIndicator size="large" color={COLORS.accent.primary} />
      </View>
    );
  }

  return (
    <Stack>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
    </Stack>
  );
}

export default function RootLayout() {
  useFonts({
    Arimo_400Regular,
    Arimo_700Bold,
    Commissioner_700Bold,
  });

  return (
    <AuthProvider>
      <RootLayoutNav />
    </AuthProvider>
  );
}
