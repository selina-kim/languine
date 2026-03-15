import { CText } from "@/components/common/CText";
import { View } from "react-native";

export default function Auth() {
  return (
    <View
      style={{
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <CText>Authentication page</CText>
    </View>
  );
}
