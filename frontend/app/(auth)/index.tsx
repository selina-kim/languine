import { CButton } from "@/components/common/CButton";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { GoogleSignin } from "@react-native-google-signin/google-signin";
import { useEffect, useState } from "react";
import { ActivityIndicator, Alert, StyleSheet, View } from "react-native";
import { exchangeGoogleToken } from "@/apis/endpoints/auth";
import { useAuth } from "@/context/AuthContext";

// Configure Google Sign-In
GoogleSignin.configure({
  webClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID,
  // iosClientId: process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID,
  offlineAccess: true, // To get refresh token
  scopes: ["openid", "profile", "email"],
});

export default function LoginScreen() {
  const { signIn } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  // Check if Google Play Services are available on Android
  useEffect(() => {
    GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true }).catch(
      (error) => {
        console.error("Play Services not available:", error);
      },
    );
  }, []);

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    try {
      // Check if user is already signed in
      await GoogleSignin.hasPlayServices();

      // Trigger Google Sign-In
      const userInfo = await GoogleSignin.signIn();

      console.log("Google Sign-In successful:", userInfo);

      // Get the ID token from the user info
      const tokens = await GoogleSignin.getTokens();
      const idToken = tokens.idToken;
      const accessToken = tokens.accessToken;

      if (!idToken) {
        throw new Error("No ID token received from Google");
      }

      // Exchange Google tokens for your backend JWT token
      const { user } = await exchangeGoogleToken(accessToken, idToken);

      console.log("Backend authentication successful:", user.email);

      // Sign in with backend token and user data
      await signIn(user);

      setIsLoading(false);
    } catch (error) {
      console.error("Google Sign-In error:", error);

      Alert.alert(
        "Authentication Error",
        error instanceof Error
          ? error.message
          : "Failed to authenticate with Google",
      );
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
