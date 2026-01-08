import { Stack } from "expo-router";
import { COLORS } from "@/constants/colors";
import { AppLogo } from "@/assets/AppLogo";
import { Pressable, View } from "react-native";
import { ProfileIcon } from "@/assets/icons/ProfileIcon";

export default function RootLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: COLORS.accent.primary,
        },
        headerTintColor: COLORS.text.primary,
        headerShadowVisible: false,
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
