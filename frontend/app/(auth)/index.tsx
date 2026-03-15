import { exchangeGoogleToken } from "@/apis/endpoints/auth";
import { AppLogo } from "@/assets/AppLogo";
import { LoginBackground } from "@/assets/LoginBackground";
import { PastaLogo } from "@/assets/PastaLogo";
import { CButton } from "@/components/common/CButton";
import { COLORS } from "@/constants/colors";
import { useAuth } from "@/context/AuthContext";
import { GoogleSignin } from "@react-native-google-signin/google-signin";
import { useEffect, useState } from "react";
import { ActivityIndicator, Alert, View } from "react-native";

// Configure Google Sign-In
GoogleSignin.configure({
  webClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID,
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
      await GoogleSignin.signIn();

      // console.log("Google Sign-In successful:", userInfo);

      // Get the ID token from the user info
      const tokens = await GoogleSignin.getTokens();
      const idToken = tokens.idToken;
      const accessToken = tokens.accessToken;

      if (!idToken) {
        throw new Error("No ID token received from Google");
      }

      // Exchange Google tokens for your backend JWT token
      const { user } = await exchangeGoogleToken(accessToken, idToken);

      // console.log("Backend authentication successful:", user.email);

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
    <View
      style={{
        backgroundColor: COLORS.accent.primary,
        height: "100%",
      }}
    >
      <View
        style={{
          position: "absolute",
          height: "100%",
          width: "100%",
        }}
      >
        <LoginBackground />
      </View>
      <View
        style={{
          width: 300,
          height: "35%",
          marginHorizontal: "auto",
        }}
      >
        <AppLogo />
      </View>
      <View
        style={{
          width: 300,
          height: "25%",
          marginHorizontal: "auto",
        }}
      >
        <PastaLogo />
      </View>
      <View
        style={{
          height: "40%",
          width: "100%",
          paddingHorizontal: 40,
          display: "flex",
          justifyContent: "center",
        }}
      >
        {isLoading ? (
          <ActivityIndicator
            size="large"
            color={COLORS.icon.fillPrimary}
            style={{ marginTop: 20 }}
          />
        ) : (
          <CButton
            onPress={handleGoogleSignIn}
            label="Sign in with Google"
            variant="google"
          />
        )}
      </View>
    </View>
  );
}
