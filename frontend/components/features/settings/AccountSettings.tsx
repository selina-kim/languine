import { useEffect, useState } from "react";
import { getCurrentUser, updateCurrentUser } from "@/apis/endpoints/users";
import { Alert } from "react-native";
import { SettingGroup } from "./SettingGroup";

export const AccountSettings = () => {
  const [newCardsPerDay, setNewCardsPerDay] = useState<string | null>(null);
  const [desiredRetention, setDesiredRetention] = useState<string | null>(null);
  const [desiredRetentionInputError, setDesiredRetentionInputError] =
    useState<string>();

  useEffect(() => {
    let isMounted = true;

    const loadUserSettings = async () => {
      const { data, error } = await getCurrentUser();

      if (!isMounted) {
        return;
      }

      if (error) {
        console.log("Failed to load user settings", error);
        return;
      }

      if (!data) {
        return;
      }

      const user = data;

      if (typeof user.new_cards_per_day === "number") {
        setNewCardsPerDay(String(user.new_cards_per_day));
      }

      if (typeof user.desired_retention === "number") {
        const percent = Math.round(user.desired_retention * 100);
        setDesiredRetention(String(percent));
      }
    };

    void loadUserSettings();

    return () => {
      isMounted = false;
    };
  }, []);

  const onSaveNewCardsPerDay = (value: string) => {
    const parsed = Number(value);
    if (!Number.isInteger(parsed) || parsed < 1) {
      Alert.alert(
        "Invalid value",
        "New cards per day must be an integer of at least 1.",
      );
      return false;
    }

    setNewCardsPerDay(value);
    void updateCurrentUser({ new_cards_per_day: parsed }).then(({ error }) => {
      if (error) {
        Alert.alert("Update failed", error);
      }
    });

    return true;
  };
  const onSaveDesiredRetention = (value: string) => {
    setDesiredRetentionInputError(undefined);

    const numeric = Number(value);
    if (numeric < 75 || numeric > 95) {
      setDesiredRetentionInputError("Value not within range");
      return false;
    }
    setDesiredRetention(value);

    const retentionRatio = numeric / 100;
    void updateCurrentUser({
      desired_retention: retentionRatio,
    }).then(({ error }) => {
      if (error) {
        Alert.alert("Update failed", error);
      }
    });

    return true;
  };

  return (
    <SettingGroup>
      <SettingGroup.Item label="Time Zone" value="EST" />
      {newCardsPerDay && (
        <SettingGroup.Item
          label="New Cards Per Day"
          description="Maximum new cards to study daily (minimum: 1)"
          value={newCardsPerDay}
          onSave={onSaveNewCardsPerDay}
        />
      )}
      {desiredRetention && (
        <SettingGroup.Item
          label="Desired Retention (%)"
          description="Target success rate for reviews (minimum: 75, maximum: 95)"
          value={desiredRetention}
          onSave={onSaveDesiredRetention}
          inputError={desiredRetentionInputError}
          isLast
        />
      )}
    </SettingGroup>
  );
};
