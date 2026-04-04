import { useState } from "react";
import { updateCurrentUser } from "@/apis/endpoints/users";
import { Alert } from "react-native";
import { SettingGroup } from "./SettingGroup";
import { ResetParametersButton } from "./ResetParametersButton";

export const OptimizationSettings = () => {
  const [autoOptimizeToggle, setAutoOptimizeToggle] = useState(true);
  const [reviews, setReviews] = useState("100");

  const onSaveReviews = (value: string) => {
    const parsed = Number(value);
    if (!Number.isInteger(parsed) || parsed < 100) {
      Alert.alert(
        "Invalid value",
        "Reviews before next optimization must be an integer of at least 100.",
      );
      return false;
    }

    setReviews(value);
    void updateCurrentUser({
      num_reviews_per_optimize: parsed,
    }).then(({ error }) => {
      if (error) {
        Alert.alert("Update failed", error);
      }
    });

    return true;
  };

  const onAutoOptimizeToggle = (value: boolean) => {
    setAutoOptimizeToggle(value);

    void updateCurrentUser({ auto_optimize: value }).then(({ error }) => {
      if (error) {
        Alert.alert("Update failed", error);
      }
    });

    return true;
  };

  return (
    <SettingGroup>
      <SettingGroup.Item
        label="Auto-Optimize Parameters"
        value={autoOptimizeToggle}
        onToggle={onAutoOptimizeToggle}
      />
      <SettingGroup.Item
        visible={autoOptimizeToggle}
        label="Reviews Before Next Optimization"
        description="Number of reviews that must be completed before parameters are updated again (minimum: 100)"
        value={reviews}
        onSave={onSaveReviews}
      />
      <ResetParametersButton />
    </SettingGroup>
  );
};
