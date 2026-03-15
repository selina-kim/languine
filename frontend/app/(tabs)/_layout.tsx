import { AppLogo } from "@/assets/AppLogo";
import { DecksIcon } from "@/assets/icons/DecksIcon";
import { HelpIcon } from "@/assets/icons/HelpIcon";
import { HomeIcon } from "@/assets/icons/HomeIcon";
import { OpenBookIcon } from "@/assets/icons/OpenBookIcon";
import { ProfileIcon } from "@/assets/icons/ProfileIcon";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { useAuth } from "@/context/AuthContext";
import { router, Tabs, usePathname } from "expo-router";
import { useState } from "react";
import { Modal, Pressable, View } from "react-native";

export default function TabLayout() {
  const { signOut, user } = useAuth();

  const [menuVisible, setMenuVisible] = useState(false);

  const handleSettings = () => {
    setMenuVisible(false);
    router.push("/(tabs)/settings"); // Navigate to settings within tabs
  };

  const handleLogout = () => {
    setMenuVisible(false);
    signOut();
  };

  const handleProfilePress = () => {
    setMenuVisible(!menuVisible);
  };

  function HeaderRight() {
    if (!user) return null;

    return (
      <Pressable
        onPress={handleProfilePress}
        style={{ marginHorizontal: 15, width: 38, height: 38 }}
      >
        <ProfileIcon />
      </Pressable>
    );
  }

  function UserDropdownMenu() {
    const pathname = usePathname();
    const showSettingsOption = pathname !== "/settings";
    return (
      <Modal
        visible={menuVisible}
        transparent
        onRequestClose={() => setMenuVisible(false)}
      >
        <Pressable
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
          }}
          onPress={() => setMenuVisible(false)}
        />
        <View
          style={{
            position: "absolute",
            top: 120,
            left: 0,
            right: 0,
            backgroundColor: COLORS.backgroundPrimary,
            paddingVertical: 10,
            ...SHADOWS.default,
            borderBottomWidth: 8,
            borderBottomColor: COLORS.accent.primary,
          }}
        >
          {showSettingsOption && (
            <Pressable
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
            </Pressable>
          )}
          <Pressable
            onPress={handleLogout}
            style={{
              paddingVertical: 14,
              alignItems: "center",
            }}
          >
            <CText style={{ top: 5 }} bold>
              Logout
            </CText>
          </Pressable>
        </View>
      </Modal>
    );
  }

  return (
    <>
      <Tabs
        screenOptions={{
          headerShown: true,
          headerStyle: {
            height: 120,
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
          tabBarActiveTintColor: COLORS.accent.secondary, // TODO?
          tabBarInactiveTintColor: COLORS.icon.outlinePrimary,
          tabBarShowLabel: false,
          tabBarInactiveBackgroundColor: COLORS.accent.primary,
          tabBarActiveBackgroundColor: COLORS.accent.primary,
          tabBarLabelPosition: "beside-icon",
          tabBarStyle: { borderTopWidth: 0 },
          sceneStyle: {
            backgroundColor: COLORS.backgroundPrimary,
          },
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            tabBarIcon: ({ color }) => <HomeIcon stroke={color} />,
          }}
        />
        <Tabs.Screen
          name="revision"
          options={{
            tabBarIcon: ({ color }) => <OpenBookIcon stroke={color} />,
          }}
        />
        <Tabs.Screen
          name="decks"
          options={{
            tabBarIcon: ({ color }) => <DecksIcon stroke={color} />,
          }}
        />
        <Tabs.Screen
          name="help"
          options={{
            tabBarIcon: ({ color }) => <HelpIcon stroke={color} />,
          }}
        />
        <Tabs.Screen
          name="settings"
          options={{
            href: null, // Hide from tab bar
          }}
        />
      </Tabs>
      {menuVisible && <UserDropdownMenu />}
    </>
  );
}
