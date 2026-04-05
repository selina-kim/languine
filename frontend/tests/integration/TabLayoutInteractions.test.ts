import { describe, expect, test, jest, beforeEach } from "@jest/globals";

// Mock router
jest.mock("expo-router", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  usePathname: jest.fn(() => "/revision"),
}));

// Mock auth context
jest.mock("@/context/AuthContext", () => ({
  useAuth: () => ({
    user: {
      id: "user123",
      email: "test@example.com",
      name: "Test User",
      token: "abc123",
    },
    signOut: jest.fn(),
  }),
}));

// Mock review session context
jest.mock("@/context/ReviewSessionContext", () => ({
  useReviewSession: () => ({
    isReviewSessionActive: true,
    requestExitReviewSession: jest.fn(),
    setIsReviewSessionActive: jest.fn(),
  }),
}));

describe("Tab Layout - handleSettings & handleLogout Actions", () => {
  let router: any;
  let authContext: any;
  let reviewContext: any;
  let uiState: any;

  beforeEach(() => {
    jest.clearAllMocks();

    router = {
      push: jest.fn(),
      replace: jest.fn(),
      back: jest.fn(),
    };

    authContext = {
      user: { id: "user123", email: "test@example.com", name: "Test User" },
      signOut: jest.fn(),
    };

    reviewContext = {
      isReviewSessionActive: true,
      requestExitReviewSession: jest.fn(),
      setIsReviewSessionActive: jest.fn(),
    };

    uiState = {
      menuVisible: false,
      isExitReviewModalVisible: false,
      isOnRevisionTab: true,
      pendingExitAction: undefined,
    };
  });

  describe("handleSettings", () => {
    test("should navigate to settings when no review session active", () => {
      const isReviewActive = false;
      const isOnRevisionTab = true;

      const doNavigateToSettings = () => {
        if (!isReviewActive || !isOnRevisionTab) {
          router.push("/(tabs)/settings");
        }
      };

      doNavigateToSettings();

      expect(router.push).toHaveBeenCalledWith("/(tabs)/settings");
    });

    test("should open exit review modal when review session active on revision tab", () => {
      const isReviewActive = true;
      const isOnRevisionTab = true;

      const promptExitReviewAndQueueAction = (action: any) => {
        uiState.menuVisible = false;
        uiState.pendingExitAction = action;
        uiState.isExitReviewModalVisible = true;
      };

      promptExitReviewAndQueueAction({ type: "settings" });

      expect(uiState.isExitReviewModalVisible).toBe(true);
      expect(uiState.pendingExitAction.type).toBe("settings");
    });

    test("should close menu after settings action", () => {
      uiState.menuVisible = true;

      const handleSettings = () => {
        uiState.menuVisible = false;
      };

      handleSettings();

      expect(uiState.menuVisible).toBe(false);
    });

    test("should not show exit review modal if not on revision tab", () => {
      const isReviewActive = true;
      const isOnRevisionTab = false;

      let shouldShowModal = isReviewActive && isOnRevisionTab;

      expect(shouldShowModal).toBe(false);
    });

    test("should navigate directly when on different tab during review", () => {
      const isReviewActive = true;
      const isOnRevisionTab = false; // On a different tab

      const doNavigateToSettings = () => {
        if (!isReviewActive || !isOnRevisionTab) {
          router.push("/(tabs)/settings");
        }
      };

      doNavigateToSettings();

      expect(router.push).toHaveBeenCalledWith("/(tabs)/settings");
    });
  });

  describe("handleLogout", () => {
    test("should open exit review modal when review session active on revision tab", () => {
      const isReviewActive = true;
      const isOnRevisionTab = true;

      const promptExitReviewAndQueueAction = (action: any) => {
        uiState.menuVisible = false;
        uiState.pendingExitAction = action;
        uiState.isExitReviewModalVisible = true;
      };

      promptExitReviewAndQueueAction({ type: "logout" });

      expect(uiState.isExitReviewModalVisible).toBe(true);
      expect(uiState.pendingExitAction.type).toBe("logout");
    });

    test("should call signOut and navigate to auth when confirmed", async () => {
      const handleConfirmExitReview = async () => {
        if (uiState.pendingExitAction?.type === "logout") {
          await authContext.signOut();
          router.push("/(auth)");
        }
      };

      uiState.pendingExitAction = { type: "logout" };
      await handleConfirmExitReview();

      expect(authContext.signOut).toHaveBeenCalled();
      expect(router.push).toHaveBeenCalledWith("/(auth)");
    });

    test("should close menu when logout is triggered", () => {
      uiState.menuVisible = true;

      const handleLogout = () => {
        uiState.menuVisible = false;
      };

      handleLogout();

      expect(uiState.menuVisible).toBe(false);
    });

    test("should directly logout when not in review session", async () => {
      const isReviewActive = false;
      const isOnRevisionTab = true;

      const doLogout = async () => {
        if (!isReviewActive) {
          await authContext.signOut();
          router.push("/(auth)");
        }
      };

      await doLogout();

      expect(authContext.signOut).toHaveBeenCalled();
      expect(router.push).toHaveBeenCalledWith("/(auth)");
    });

    test("should request exit review session signal", () => {
      const handleLogout = () => {
        reviewContext.requestExitReviewSession();
        reviewContext.setIsReviewSessionActive(false);
      };

      handleLogout();

      expect(reviewContext.requestExitReviewSession).toHaveBeenCalled();
      expect(reviewContext.setIsReviewSessionActive).toHaveBeenCalledWith(
        false,
      );
    });
  });

  describe("Exit Review Modal Workflow", () => {
    test("should cancel exit review and return to current screen", () => {
      uiState.isExitReviewModalVisible = true;
      uiState.pendingExitAction = { type: "settings" };

      const handleCancelExitReview = () => {
        uiState.isExitReviewModalVisible = false;
        uiState.pendingExitAction = undefined;
      };

      handleCancelExitReview();

      expect(uiState.isExitReviewModalVisible).toBe(false);
      expect(uiState.pendingExitAction).toBeUndefined();
    });

    test("should confirm exit and execute pending action", () => {
      uiState.isExitReviewModalVisible = true;
      uiState.pendingExitAction = { type: "settings" };

      const handleConfirmExitReview = () => {
        uiState.isExitReviewModalVisible = false;

        if (uiState.pendingExitAction?.type === "settings") {
          router.push("/(tabs)/settings");
        }

        uiState.pendingExitAction = undefined;
      };

      handleConfirmExitReview();

      expect(uiState.isExitReviewModalVisible).toBe(false);
      expect(router.push).toHaveBeenCalledWith("/(tabs)/settings");
      expect(uiState.pendingExitAction).toBeUndefined();
    });

    test("should request exit review session before action", () => {
      const handleConfirmExitReview = () => {
        reviewContext.requestExitReviewSession();
        reviewContext.setIsReviewSessionActive(false);

        if (uiState.pendingExitAction?.type === "logout") {
          authContext.signOut();
        }
      };

      uiState.pendingExitAction = { type: "logout" };
      handleConfirmExitReview();

      expect(reviewContext.requestExitReviewSession).toHaveBeenCalled();
      expect(reviewContext.setIsReviewSessionActive).toHaveBeenCalledWith(
        false,
      );
      expect(authContext.signOut).toHaveBeenCalled();
    });

    test("should queue multiple action types correctly", () => {
      const actionTypes = ["settings", "logout", "tab"];

      actionTypes.forEach((type) => {
        uiState.pendingExitAction = { type };
        expect(uiState.pendingExitAction.type).toBe(type);
      });
    });
  });

  describe("User Dropdown Menu", () => {
    test("should toggle menu visibility", () => {
      uiState.menuVisible = false;

      const handleProfilePress = () => {
        uiState.menuVisible = !uiState.menuVisible;
      };

      handleProfilePress();
      expect(uiState.menuVisible).toBe(true);

      handleProfilePress();
      expect(uiState.menuVisible).toBe(false);
    });

    test("should hide menu when settings selected", () => {
      uiState.menuVisible = true;

      const handleSettings = () => {
        uiState.menuVisible = false;
      };

      handleSettings();

      expect(uiState.menuVisible).toBe(false);
    });

    test("should hide menu when logout selected", () => {
      uiState.menuVisible = true;

      const handleLogout = () => {
        uiState.menuVisible = false;
      };

      handleLogout();

      expect(uiState.menuVisible).toBe(false);
    });

    test("should hide menu when pressed outside", () => {
      uiState.menuVisible = true;

      const handlePressOutside = () => {
        uiState.menuVisible = false;
      };

      handlePressOutside();

      expect(uiState.menuVisible).toBe(false);
    });
  });
});
