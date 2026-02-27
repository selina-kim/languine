import { NoDecksBanner } from "@/components/features/decks/NoDecksBanner";
import { View } from "react-native";

export default function Decks() {
  return (
    <View
      style={{
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
        padding: 10,
      }}
    >
      <NoDecksBanner />
    </View>
  );
}
