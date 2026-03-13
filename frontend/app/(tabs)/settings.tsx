import { View, ScrollView} from "react-native";
import { DeleteButton } from "@/components/common/DeleteButton";
import { DisplayNameSettings } from "@/components/features/settings/DisplayNameSetting";
import { OptimizationSettings } from "@/components/features/settings/OptimizationSettings";
import { UserSettings } from "@/components/features/settings/UserSettings";
import { EditModal } from "@/components/features/settings/EditModal";
import React, { useState } from "react";

export type SettingsValues = {
  displayName: string;
  timeZone: string;
  newCardsPerDay: number;
  retrievability: number;
  reviewsBeforeNextOptimization: number;
};

const initialSettings: SettingsValues = {
  displayName: "Tinu",
  timeZone: "EST",
  newCardsPerDay: 10,
  retrievability: 90,
  reviewsBeforeNextOptimization: 100,
};

const SETTING_LABELS: Record<keyof SettingsValues, { label: string; description?: string }> = {
  displayName: { label: "Display Name", description: "Your profile name" },
  timeZone: { label: "Time Zone", description: "Your local time zone for scheduling" },
  newCardsPerDay: { label: "New Cards Per Day", description: "Maximum new cards to study daily\nmin: 1" },
  retrievability: { label: "Retrievability %", description: "Target success rate for reviews\nmin: 75  max: 95" },
  reviewsBeforeNextOptimization: { label: "Reviews Before Optimization", description: "Number of reviews that must be completed before parameters are updated again\nmin: 100" },
};


export default function Settings() {
  const [settingsState, setSettingsState] = useState<SettingsValues>(initialSettings);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalKey, setModalKey] = useState<keyof SettingsValues | null>(null);
  const [modalValue, setModalValue] = useState("");

  const handleSave = (key: keyof SettingsValues, value: string) => {
    setSettingsState((prev) => ({
      ...prev,
      [key]: typeof prev[key] === "number" ? Number(value) : value,
    }));
  };

  const openModal = (key: keyof SettingsValues) => {
    setModalKey(key);
    setModalValue(String(settingsState[key]));
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
    setModalKey(null);
    setModalValue("");
  };

  return (
    <ScrollView
      contentContainerStyle={{
        paddingTop: 30,
        paddingHorizontal: 30,
      }}
      style={{ flex: 1 }}
    >
      {/* Block 1 */}
      <DisplayNameSettings
        displayName={settingsState.displayName}
        onEdit={() => openModal("displayName")}
      />

      {/* Block 2 */}
      <UserSettings
        values={{
          timeZone: settingsState.timeZone,
          newCardsPerDay: settingsState.newCardsPerDay,
          retrievability: settingsState.retrievability,
        }}
        onEdit={(key) => openModal(key)}
      />

      {/* Block 3 */}
      <OptimizationSettings
        reviewsBeforeNextOptimization={settingsState.reviewsBeforeNextOptimization}
        onEdit={() => openModal("reviewsBeforeNextOptimization")}
      />

      <View style={{ marginTop: 60 }}>
        <DeleteButton
          label="Delete Account"
          onConfirm={() => {
            // Handle account deletion logic here
          }}
          submitLabel="Delete Account"
          confirmDescription="This action will permanently delete your account and all associated data"
        />
      </View>

      {/* Modal */}
      <EditModal
        visible={modalVisible}
        header={modalKey ? SETTING_LABELS[modalKey].label : ""}
        subheader={modalKey ? SETTING_LABELS[modalKey].description : ""}
        value={modalValue}
        onChange={setModalValue}
        onClose={closeModal}
        onSave={() => {
          if (modalKey) handleSave(modalKey, modalValue);
          closeModal();
        }}
      />
    </ScrollView>
  );
}