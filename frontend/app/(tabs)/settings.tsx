import { AccountSettings } from "@/components/features/settings/AccountSettings";
import { DeleteAccountButton } from "@/components/features/settings/DeleteAccountButton";
import { OptimizationSettings } from "@/components/features/settings/OptimizationSettings";
import { ProfileSettings } from "@/components/features/settings/ProfileSettings";
import { useFocusEffect } from "@react-navigation/native";
import React, { useCallback, useState } from "react";
import { ScrollView } from "react-native";

export default function Settings() {
  const [renderKey, setRenderKey] = useState(0);

  useFocusEffect(
    useCallback(() => {
      setRenderKey((prev) => prev + 1);
    }, []),
  );

  return (
    <ScrollView
      key={renderKey}
      contentContainerStyle={{
        paddingTop: 30,
        paddingHorizontal: 30,
        display: "flex",
        rowGap: 20,
      }}
    >
      <ProfileSettings />
      <AccountSettings />
      <OptimizationSettings />
      <DeleteAccountButton />
    </ScrollView>
  );
}
