import { AppLogo } from "@/assets/AppLogo";
import { ProfileIcon } from "@/assets/icons/ProfileIcon";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { Arimo_400Regular, Arimo_700Bold } from "@expo-google-fonts/arimo";
import { useFonts } from "expo-font";
import { Stack } from "expo-router";
import { Pressable, View } from "react-native";

export default function RootLayout() {
  useFonts({
    Arimo_400Regular,
    Arimo_700Bold,
  });

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
        headerRight: () => (
          <Pressable
            onPress={() => console.log("profile clicked")}
            style={{ marginHorizontal: 15, width: 38 }}
          >
            <ProfileIcon />
          </Pressable>
        ),
      }}
    >
      <Stack.Screen name="(tabs)" options={{ headerShown: true }} />
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
    </Stack>
  );
}
