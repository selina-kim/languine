import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { View } from "react-native";

type LastReviewedDeckItemProps = {
  deckName: string;
  lastReviewed: string;
};

export const LastReviewedDeckItem = ({
  deckName,
  lastReviewed,
}: LastReviewedDeckItemProps) => {
  return (
    <View style={{ width: "100%" }}>
      <View
        style={{
          rowGap: "10px",
          paddingVertical: 10,
          paddingHorizontal: 25,
        }}
      >
        <View
          style={{
            paddingVertical: 10,
            paddingHorizontal: 25,
            borderWidth: 3,
            borderColor: COLORS.icon.outlineSecondary,
            borderRadius: 16,
            ...SHADOWS.default,
          }}
        >
          <CText variant="containerLabel" bold>
            {deckName}
          </CText>
          <CText
            style={{
              color: COLORS.text.secondary,
            }}
          >
            Last reviewed: {lastReviewed}
          </CText>
        </View>
      </View>
    </View>
  );
};
