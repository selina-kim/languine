import { CButton } from "@/components/common/CButton";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import * as Google from "expo-auth-session/providers/google";
import * as WebBrowser from "expo-web-browser";
import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Alert, StyleSheet, View } from "react-native";
import { useAuth } from "../context/AuthContext";

// Required for web-based OAuth flows
WebBrowser.maybeCompleteAuthSession();

export default function LoginScreen() {
  const { signIn } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  // Configure Google OAuth request
  const [, response, promptAsync] = Google.useAuthRequest({
    webClientId: process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID,
    // iosClientId: googleAuthConfig.iosClientId,
    // androidClientId: googleAuthConfig.androidClientId,
    scopes: ["profile", "email"],
  });

  const handleSuccessfulLogin = useCallback(
    async (authentication: any) => {
      try {
        // Get user info from Google
        const userInfoResponse = await fetch(
          "https://www.googleapis.com/userinfo/v2/me",
          {
            headers: { Authorization: `Bearer ${authentication.accessToken}` },
          },
        );
        const userInfo = await userInfoResponse.json();

        console.log("User Info:", userInfo);
        console.log("Access Token:", authentication.accessToken);

        // TODO: Send the access token to your backend to verify and create/login user
        // Example API call:
        // const response = await fetch('YOUR_BACKEND_URL/auth/google', {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify({
        //     accessToken: authentication.accessToken,
        //     idToken: authentication.idToken,
        //   }),
        // });
        // const data = await response.json();

        // Store the user session/token (you might want to use AsyncStorage or SecureStore)
        // await SecureStore.setItemAsync('userToken', data.token);

        // Sign in the user - this will automatically redirect to tabs
        signIn({
          ...userInfo,
          accessToken: authentication.accessToken,
          idToken: authentication.idToken,
        });

        setIsLoading(false);
      } catch (error) {
        console.error("Error fetching user info:", error);
        Alert.alert("Error", "Failed to get user information");
        setIsLoading(false);
      }
    },
    [signIn],
  );

  // Handle the OAuth response
  useEffect(() => {
    if (response?.type === "success") {
      const { authentication } = response;
      handleSuccessfulLogin(authentication);
    } else if (response?.type === "error") {
      Alert.alert(
        "Authentication Error",
        response.error?.message || "Failed to authenticate",
      );
      setIsLoading(false);
    } else if (response?.type === "dismiss" || response?.type === "cancel") {
      setIsLoading(false);
    }
  }, [response, handleSuccessfulLogin]);

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    try {
      await promptAsync();
    } catch (error) {
      console.error("Error prompting Google sign-in:", error);
      Alert.alert("Error", "Failed to open Google sign-in");
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <CText style={styles.title} bold>
          Welcome to Languine
        </CText>
        <CText style={styles.subtitle}>
          Sign in to access your language learning decks
        </CText>

        {isLoading ? (
          <ActivityIndicator
            size="large"
            color={COLORS.accent.primary}
            style={styles.loader}
          />
        ) : (
          <CButton
            onPress={handleGoogleSignIn}
            variant="primary"
            label="Sign in with Google"
          />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.backgroundPrimary,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
  },
  content: {
    width: "100%",
    maxWidth: 400,
    alignItems: "center",
  },
  title: {
    fontSize: 32,
    color: COLORS.text.primary,
    marginBottom: 12,
    textAlign: "center",
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.text.secondary,
    marginBottom: 40,
    textAlign: "center",
  },
  googleButton: {
    width: "100%",
    backgroundColor: COLORS.accent.primary,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 8,
    alignItems: "center",
  },
  buttonText: {
    color: COLORS.text.primary,
    fontSize: 16,
  },
  loader: {
    marginTop: 20,
  },
});
