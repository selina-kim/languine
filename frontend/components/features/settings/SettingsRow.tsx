import { EditIcon } from "@/assets/icons/EditIcon";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { Pressable, View } from "react-native";

interface SettingsRowProps {
  label: string;
  value: string | number;
  onPress?: () => void;
  isLast?: boolean;
}

export const SettingsRow = ({
  label,
  value,
  onPress,
  isLast = false,
}: SettingsRowProps) => {
  return (
    <View
      style={{
        borderBottomWidth: isLast ? 0 : 1,
        borderBottomColor: COLORS.icon.outlinePrimary,
        display: "flex",
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <View>
        <CText bold>{label}</CText>
        <CText style={{ color: COLORS.text.secondary }}>{value}</CText>
      </View>
      <Pressable
        onPress={onPress}
        style={{ width: 25, height: 25, alignItems: "center" }}
      >
        <EditIcon />
      </Pressable>
    </View>
  );
};
