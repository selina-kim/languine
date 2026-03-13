import React, { useState } from "react";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { View } from "react-native";
import { CButton } from "@/components/common/CButton";
import { DeleteButton } from "@/components/common/DeleteButton";
import { SettingsRow } from "@/components/features/settings/SettingsRow";
import { CSwitch } from "@/components/common/CSwitch";

type OptimizationSettingsProps = {
  reviewsBeforeNextOptimization: number;
  onEdit: () => void;
  onResetParameters?: () => void;
};

export function OptimizationSettings({
  reviewsBeforeNextOptimization,
  onEdit,
  onResetParameters,
}: OptimizationSettingsProps) {
  const [autoOptimizeEnabled, setAutoOptimizeEnabled] = useState(true);

  // debug: ensure imported components are defined
  // eslint-disable-next-line no-console
  console.log("OptimizationSettings imports:", { CSwitchDefined: typeof CSwitch !== "undefined", SettingsRowDefined: typeof SettingsRow !== "undefined", CButtonDefined: typeof CButton !== "undefined" });

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
      <View
        style={{
          paddingHorizontal: 25,
          paddingTop: 15,
          paddingBottom: 20,
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <CText bold style={{ fontSize: 16, color: COLORS.text.primary }}>
          Auto-Optimize Parameters
        </CText>
        <CSwitch
          value={autoOptimizeEnabled}
          onChange={setAutoOptimizeEnabled}
        />
      </View>

      {autoOptimizeEnabled && (
        <View style={{ paddingHorizontal: 25 }}>
          <View 
            style={{ 
              borderTopWidth: 2,
              borderTopColor: COLORS.icon.outlineSecondary,
            }}
          >
          <SettingsRow
            label="Reviews Before Next Optimization"
            value={reviewsBeforeNextOptimization}
            onPress={onEdit}
            isLast={true}
          />
          </View>
        </View>
      )}

      <View 
        style={{ 
          paddingHorizontal: 25, 
        }}
      >
        <View
          style={{
            borderTopWidth: 2,
            borderTopColor: COLORS.icon.outlineSecondary,
            paddingVertical: 20,
          }}
        >
          <DeleteButton
            label="Reset Parameters"
            onConfirm={() => {
              // onResetParameters should handle the logic to reset parameters to default values
            }}
            deleteVariant="deleteSecondary"
            submitLabel="Reset Parameters"
            confirmDescription="This action will reset all optimization parameters to their default values"
          />
        </View>
      </View>
    </View>
  );
}