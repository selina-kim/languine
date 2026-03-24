import { AppLogo } from "@/assets/AppLogo";
import { DecksIcon } from "@/assets/icons/DecksIcon";
import { HelpIcon } from "@/assets/icons/HelpIcon";
import { HomeIcon } from "@/assets/icons/HomeIcon";
import { OpenBookIcon } from "@/assets/icons/OpenBookIcon";
import { ProfileIcon } from "@/assets/icons/ProfileIcon";
import { Modal } from "@/components/common/Modal";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { useAuth } from "@/context/AuthContext";
import {
  ReviewSessionProvider,
  useReviewSession,
} from "@/context/ReviewSessionContext";
import { router, Tabs, usePathname } from "expo-router";
import { useState } from "react";
import { Modal as RNModal, Pressable, View } from "react-native";

type PendingExitAction =
  | { type: "tab"; path: "/(tabs)" | "/(tabs)/decks" | "/(tabs)/help" }
  | { type: "settings" }
  | { type: "logout" };

export default function TabLayout() {
  return (
    <ReviewSessionProvider>
      <TabLayoutContent />
    </ReviewSessionProvider>
  );
}

function TabLayoutContent() {
  const { signOut, user } = useAuth();
  const {
    isReviewSessionActive,
    setIsReviewSessionActive,
    requestExitReviewSession,
  } = useReviewSession();
  const pathname = usePathname();
  const isOnRevisionTab = pathname === "/revision";

  const [menuVisible, setMenuVisible] = useState(false);
  const [isExitReviewModalVisible, setIsExitReviewModalVisible] =
    useState(false);
  const [pendingExitAction, setPendingExitAction] = useState<
    PendingExitAction | undefined
  >();

  const doNavigateToSettings = () => {
    router.push("/(tabs)/settings");
  };

  const doLogout = () => {
    signOut();
    router.push("/(auth)");
  };

  const promptExitReviewAndQueueAction = (action: PendingExitAction) => {
    setMenuVisible(false);
    setPendingExitAction(action);
    setIsExitReviewModalVisible(true);
  };

  const handleSettings = () => {
    if (isReviewSessionActive && isOnRevisionTab) {
      promptExitReviewAndQueueAction({ type: "settings" });
      return;
    }

    doNavigateToSettings();
    setMenuVisible(false);
  };

  const handleLogout = () => {
    if (isReviewSessionActive && isOnRevisionTab) {
      promptExitReviewAndQueueAction({ type: "logout" });
      return;
    }

    doLogout();
    setMenuVisible(false);
  };

  const handleProfilePress = () => {
    setMenuVisible(!menuVisible);
  };

  const handleTabPress = (
    targetPath: "/(tabs)" | "/(tabs)/decks" | "/(tabs)/help",
    event: { preventDefault: () => void },
  ) => {
    if (!isReviewSessionActive || !isOnRevisionTab) {
      return;
    }

    event.preventDefault();
    promptExitReviewAndQueueAction({ type: "tab", path: targetPath });
  };

  const handleConfirmExitReview = () => {
    setIsExitReviewModalVisible(false);

    if (!pendingExitAction) {
      return;
    }

    requestExitReviewSession();
    setIsReviewSessionActive(false);

    if (pendingExitAction.type === "tab") {
      router.push(pendingExitAction.path);
    }

    if (pendingExitAction.type === "settings") {
      doNavigateToSettings();
    }

    if (pendingExitAction.type === "logout") {
      doLogout();
    }

    setPendingExitAction(undefined);
  };

  const handleCancelExitReview = () => {
    setIsExitReviewModalVisible(false);
    setPendingExitAction(undefined);
  };

  const HeaderRight = () => {
    if (!user) return null;

    return (
      <Pressable
        onPress={handleProfilePress}
        style={{ marginHorizontal: 15, width: 38, height: 38 }}
      >
        <ProfileIcon />
      </Pressable>
    );
  };

  const UserDropdownMenu = () => {
    const showSettingsOption = pathname !== "/settings";
    return (
      <RNModal
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
            top: 120,
            backgroundColor: COLORS.background.primary,
            ...SHADOWS.default,
            borderBottomWidth: 8,
            borderBottomColor: COLORS.accent.primary,
          }}
        >
          {showSettingsOption && (
            <Pressable
              onPress={handleSettings}
              style={{
                height: 60,
                justifyContent: "center",
                alignItems: "center",
                borderBottomWidth: 1,
                borderBottomColor: "#D0D0D0",
              }}
            >
              <CText bold>User Settings</CText>
            </Pressable>
          )}
          <Pressable
            onPress={handleLogout}
            style={{
              height: 60,
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <CText bold>Sign out</CText>
          </Pressable>
        </View>
      </RNModal>
    );
  };

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
            backgroundColor: COLORS.background.primary,
          },
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            tabBarIcon: ({ color }) => <HomeIcon stroke={color} />,
          }}
          listeners={{
            tabPress: (event) => handleTabPress("/(tabs)", event),
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
          listeners={{
            tabPress: (event) => handleTabPress("/(tabs)/decks", event),
          }}
        />
        <Tabs.Screen
          name="help"
          options={{
            tabBarIcon: ({ color }) => <HelpIcon stroke={color} />,
          }}
          listeners={{
            tabPress: (event) => handleTabPress("/(tabs)/help", event),
          }}
        />
        <Tabs.Screen name="settings" options={{ href: null }} />
      </Tabs>
      {menuVisible && <UserDropdownMenu />}
      <Modal
        visible={isExitReviewModalVisible}
        header="Are you sure?"
        subheader="You will be exiting your review session"
        submitLabel="Exit Session"
        onSubmit={handleConfirmExitReview}
        closeLabel="Stay"
        onClose={handleCancelExitReview}
      />
    </>
  );
}
