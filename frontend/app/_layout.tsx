import { AppLogo } from "@/assets/AppLogo";
import { ProfileIcon } from "@/assets/icons/ProfileIcon";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { Arimo_400Regular, Arimo_700Bold } from "@expo-google-fonts/arimo";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import { ActivityIndicator, Pressable, View } from "react-native";
import { AuthProvider, useAuth } from "@/context/AuthContext";

function HeaderRight() {
  const { signOut, user } = useAuth();

  // Only show profile icon if user is authenticated
  if (!user) return null;

  return (
    <Pressable onPress={signOut} style={{ marginHorizontal: 15, width: 38 }}>
      <ProfileIcon />
    </Pressable>
  );
}

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
          backgroundColor: COLORS.backgroundPrimary,
        }}
      >
        <ActivityIndicator size="large" color={COLORS.accent.primary} />
      </View>
    );
  }

  return (
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: COLORS.accent.primary,
          ...SHADOWS.default,
        },
        headerTintColor: COLORS.text.primary,
        headerTitle: () => (
          <View style={{ width: 100 }}>
            <AppLogo />
          </View>
        ),
        headerRight: () => <HeaderRight />,
      }}
    >
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)" options={{ headerShown: true }} />
    </Stack>
  );
}

export default function RootLayout() {
  useFonts({
    Arimo_400Regular,
    Arimo_700Bold,
  });

  return (
    <AuthProvider>
      <RootLayoutNav />
    </AuthProvider>
  );
}
