import { ScrollView, View } from "react-native";

interface SingleDeckViewProps {
  deck_id: string;
}

export default function SingleDeckView({ deck_id }: SingleDeckViewProps) {
  return (
    <View style={{ height: "100%" }}>
      <ScrollView
        contentContainerStyle={{
          display: "flex",
          justifyContent: "flex-start",
          alignItems: "center",
          paddingHorizontal: 25,
          paddingVertical: 25,
          rowGap: 20,
        }}
      ></ScrollView>
    </View>
  );
}
