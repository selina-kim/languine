import { useState } from "react";
import { SettingGroup } from "./SettingGroup";

export const AccountSettings = () => {
  const [newCardsPerDay, setNewCardsPerDay] = useState("10");
  const [desiredRetention, setDesiredRetention] = useState("90");
  const [desiredRetentionInputError, setDesiredRetentionInputError] =
    useState<string>();

  const onSaveNewCardsPerDay = (value: string) => {
    // TODO
    setNewCardsPerDay(value);
    return true;
  };
  const onSaveDesiredRetention = (value: string) => {
    setDesiredRetentionInputError(undefined);

    if (Number(value) < 75 || Number(value) > 95) {
      setDesiredRetentionInputError("Value not within range");
      return false;
    }
    // TODO
    setDesiredRetention(value);
    return true;
  };

  return (
    <SettingGroup>
      <SettingGroup.Item label="Time Zone" value="EST" />
      <SettingGroup.Item
        label="New Cards Per Day"
        description="Maximum new cards to study daily (minimum: 1)"
        value={newCardsPerDay}
        onSave={onSaveNewCardsPerDay}
      />
      <SettingGroup.Item
        label="Desired Retention (%)"
        description="Target success rate for reviews (minimum: 75, maximum: 95)"
        value={desiredRetention}
        onSave={onSaveDesiredRetention}
        inputError={desiredRetentionInputError}
        isLast
      />
    </SettingGroup>
  );
};
