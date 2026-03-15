import { useState } from "react";
import { SettingGroup } from "./SettingGroup";

export const AccountSettings = () => {
  const [newCardsPerDay, setNewCardsPerDay] = useState("10");
  const [retrievability, setRetrievability] = useState("90");
  const [retrievabilityInputError, setRetrievabilityInputError] =
    useState<string>();

  const onSaveNewCardsPerDay = (value: string) => {
    // TODO
    setNewCardsPerDay(value);
    return true;
  };
  const onSaveRetrievability = (value: string) => {
    setRetrievabilityInputError(undefined);

    if (Number(value) < 75 || Number(value) > 95) {
      setRetrievabilityInputError("Value not within range");
      return false;
    }
    // TODO
    setRetrievability(value);
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
        label="Retrievability %"
        description="Target success rate for reviews (minimum: 75, maximum: 95)"
        value={retrievability}
        onSave={onSaveRetrievability}
        inputError={retrievabilityInputError}
        isLast
      />
    </SettingGroup>
  );
};
