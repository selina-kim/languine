import React from "react";
import { Pressable, View } from "react-native";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { EditIcon } from "@/assets/icons/EditIcon";
import { SHADOWS } from "@/constants/shadows";

type SettingKey = "timeZone" | "newCardsPerDay" | "retrievability";

export type UserSettingsValues = {
  timeZone: string;
  newCardsPerDay: number;
  retrievability: number;
};

interface SettingConfig<K extends SettingKey> {
  key: K;
  label: string;
}

interface UserSettingsProps {
  values: UserSettingsValues;
  onEdit: (key: SettingKey) => void;
  onSave?: (key: SettingKey, value: string) => void;
}

const SETTINGS_CONFIG: SettingConfig<SettingKey>[] = [
  { key: "timeZone", label: "Time Zone" },
  { key: "newCardsPerDay", label: "New Cards Per Day" },
  { key: "retrievability", label: "Retrievability %" },
];

export const UserSettings = ({ values, onEdit }: UserSettingsProps) => {
  return (
    <View
      style={{
        marginTop: 20,
        width: "100%",
        borderWidth: 3,
        borderColor: COLORS.icon.outlineSecondary,
        borderRadius: 16,
        backgroundColor: COLORS.backgroundPrimary,
        ...SHADOWS.default,
      }}
    >
      <View style={{ paddingHorizontal: 25 }}>
        {SETTINGS_CONFIG.map((setting, index) => (
          <View
            key={setting.key}
            style={{
              borderBottomWidth: index === SETTINGS_CONFIG.length - 1 ? 0 : 2,
              borderBottomColor: COLORS.icon.outlineSecondary,
              paddingVertical: 15,
              flexDirection: "row",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <View style={{ flex: 1, paddingRight: 8 }}>
              <CText bold>{setting.label}</CText>
              <CText style={{ color: COLORS.text.secondary }}>
                {String(values[setting.key])}
              </CText>
            </View>

            {setting.key !== "timeZone" && (
              <Pressable
                onPress={() => onEdit(setting.key)}
                style={{ width: 25, alignItems: "center" }}
              >
                <EditIcon />
              </Pressable>
            )}
          </View>
        ))}
      </View>
    </View>
  );
};
