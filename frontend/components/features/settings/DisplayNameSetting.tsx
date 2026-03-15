import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { View } from "react-native";
import { SettingsRow } from "./SettingsRow";

type DisplayNameSettingsProps = {
  displayName: string;
  onEdit?: () => void;
};

export const DisplayNameSettings = ({
  displayName,
  onEdit,
}: DisplayNameSettingsProps) => {
  return (
    <View
      style={{
        marginTop: 10,
        width: "100%",
        borderWidth: 3,
        borderColor: COLORS.icon.outlineSecondary,
        borderRadius: 16,
        backgroundColor: COLORS.backgroundPrimary,
        ...SHADOWS.default,
      }}
    >
      <View style={{ paddingHorizontal: 25 }}>
        <SettingsRow
          label="Display Name"
          value={displayName}
          onPress={onEdit}
          isLast={true}
        />
      </View>
    </View>
  );
};
