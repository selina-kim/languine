import { useAuth } from "@/context/AuthContext";
import { useState } from "react";
import { SettingGroup } from "./SettingGroup";

export const ProfileSettings = () => {
  const { user } = useAuth();

  const [displayName, setDisplayName] = useState(user?.name || "");

  const onSave = (value: string) => {
    // TODO
    setDisplayName(value);
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
