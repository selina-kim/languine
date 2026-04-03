import { useAuth } from "@/context/AuthContext";
import { updateCurrentUser } from "@/apis/endpoints/users";
import { useState } from "react";
import { Alert } from "react-native";
import { SettingGroup } from "./SettingGroup";

export const ProfileSettings = () => {
  const { user, signIn } = useAuth();

  const [displayName, setDisplayName] = useState(user?.name || "");

  const onSave = (value: string) => {
    if (!user) {
      Alert.alert("Error", "You must be logged in to update your profile.");
      return false;
    }

    const trimmed = value.trim();
    if (!trimmed) {
      Alert.alert("Invalid name", "Display name cannot be empty.");
      return false;
    }

    setDisplayName(trimmed);

    // Optimistically update auth state and send to backend
    void updateCurrentUser({ display_name: trimmed }).then(({ error }) => {
      if (error) {
        Alert.alert("Update failed", error);
      }
    });

    void signIn({ ...user, name: trimmed });

    return true;
  };

  return (
    <>
      <SettingGroup>
        <SettingGroup.Item
          label="Display Name"
          description="Your profile name"
          value={displayName}
          onSave={onSave}
          isLast
        />
      </SettingGroup>
    </>
  );
};
