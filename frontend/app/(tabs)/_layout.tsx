import { DecksIcon } from "@/assets/icons/DecksIcon";
import { HelpIcon } from "@/assets/icons/HelpIcon";
import { HomeIcon } from "@/assets/icons/HomeIcon";
import { OpenBookIcon } from "@/assets/icons/OpenBookIcon";
import { COLORS } from "@/constants/colors";
import { Tabs } from "expo-router";

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
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
  );
}
