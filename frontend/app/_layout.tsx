import { AppLogo } from "@/assets/AppLogo";
import { ProfileIcon } from "@/assets/icons/ProfileIcon";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { Arimo_400Regular, Arimo_700Bold } from "@expo-google-fonts/arimo";
import { useFonts } from "expo-font";
import { Stack, useRouter } from "expo-router";
import { Pressable, View, Modal, TouchableOpacity, Text } from "react-native";
import { useState } from "react";
import { CText } from "@/components/common/CText";

export default function RootLayout() {
  const [menuVisible, setMenuVisible] = useState(false);
  const router = useRouter();

  useFonts({
    Arimo_400Regular,
    Arimo_700Bold,
  });

  const handleSettings = () => {
    setMenuVisible(false);
    router.push("/(tabs)/settings"); // Navigate to settings within tabs
  };

  const handleLogout = () => {
    setMenuVisible(false);
    // Add your logout logic here
    console.log("Logout pressed");
    router.push("/(auth)/login"); // Redirect to login after logout
  };

  return (
    <>
      <Stack>
        <Stack.Screen
          name="(tabs)"
          options={{
            headerShown: true,
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
                onPress={() => setMenuVisible(true)}
                style={{ marginHorizontal: 15, width: 38 }}
              >
                <ProfileIcon />
              </Pressable>
            ),
          }}
        />
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      </Stack>

      <Modal
        visible={menuVisible}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setMenuVisible(false)}
      >
        <Pressable style={{ flex: 1 }} onPress={() => setMenuVisible(false)}>
          <View
            style={{
              position: "absolute",
              top: 65,
              left: 0,
              right: 0,
              backgroundColor: COLORS.backgroundPrimary,
              paddingVertical: 10,
              ...SHADOWS.default,
              borderBottomWidth: 8,
              borderBottomColor: COLORS.accent.primary,
            }}
          >
            <TouchableOpacity
              onPress={handleSettings}
              style={{
                paddingVertical: 14,
                alignItems: "center",
                borderBottomWidth: 1,
                borderBottomColor: "#D0D0D0",
              }}
            >
              <CText style={{ top: -3 }} bold>
                User Settings
              </CText>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={handleLogout}
              style={{
                paddingVertical: 14,
                alignItems: "center",
              }}
            >
              <CText style={{ top: 5 }} bold>
                Logout
              </CText>
            </TouchableOpacity>
          </View>
        </Pressable>
      </Modal>
    </>
  );
}
