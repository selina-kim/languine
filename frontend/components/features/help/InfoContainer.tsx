import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { View } from "react-native";

export const InfoContainer = () => {
  return (
    <View style={{ width: "100%" }}>
      <View
        style={{
          rowGap: "10px",
          paddingTop: 30,
          paddingBottom: 10,
          paddingHorizontal: 25,
        }}
      >
        <View
          style={{
            padding: 25,
            borderWidth: 2,
            borderColor: COLORS.icon.outlinePrimary,
            borderRadius: 16,
          }}
        >
          <CText variant="containerLabel" style={{ paddingBottom: 10 }}>
            Welcome to Languine
          </CText>
          <CText
            style={{
              color: COLORS.text.secondary,
              paddingBottom: 20,
            }}
          >
            Your comprehensive language learning flashcard application!
          </CText>
          <CText style={{ color: COLORS.text.secondary }}>
            Languine uses spaced repetition to help you learn and retain
            vocabulary more effectively. The app intelligently schedules card
            reviews based on your performance, ensuring optimal learning.
          </CText>
        </View>
      </View>
    </View>
  );
};
