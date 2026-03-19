import { CButton } from "@/components/common/CButton";
import { useState } from "react";
import { SettingGroup } from "./SettingGroup";
import { ResetParametersButton } from "./ResetParametersButton";

export const OptimizationSettings = () => {
  const [autoOptimizeToggle, setAutoOptimizeToggle] = useState(true);
  const [reviews, setReviews] = useState("100");

  const onSaveReviews = (value: string) => {
    // TODO
    setReviews(value);
    return true;
  };

  const onAutoOptimizeToggle = (value: boolean) => {
    // TODO
    console.log("autoOptimizeToggle:", value);
    setAutoOptimizeToggle(value);
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
