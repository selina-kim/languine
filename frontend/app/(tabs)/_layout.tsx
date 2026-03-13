import { AppLogo } from "@/assets/AppLogo";
import { DecksIcon } from "@/assets/icons/DecksIcon";
import { HelpIcon } from "@/assets/icons/HelpIcon";
import { HomeIcon } from "@/assets/icons/HomeIcon";
import { OpenBookIcon } from "@/assets/icons/OpenBookIcon";
import { ProfileIcon } from "@/assets/icons/ProfileIcon";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { useAuth } from "@/context/AuthContext";
import { Tabs } from "expo-router";
import { Pressable, View } from "react-native";

function HeaderRight() {
  const { signOut, user } = useAuth();

  const handleProfilePress = () => {
    signOut(); // TODO: temporary, replace with profile page later
  };

  if (!user) return null;

  return (
    <Pressable
      onPress={handleProfilePress}
      style={{ marginHorizontal: 15, width: 38 }}
    >
      <ProfileIcon />
    </Pressable>
  );
}

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
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
    </Tabs>
  );
}
