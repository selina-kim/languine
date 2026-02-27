import { CText } from "@/components/common/CText";
import { View } from "react-native";

export default function Help() {
  return (
    <View
      style={{
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <CText>help page</CText>
    </View>
  );
}
