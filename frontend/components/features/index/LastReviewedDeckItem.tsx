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
    <View
      style={{
        paddingVertical: 10,
        paddingHorizontal: 25,
        borderWidth: 3,
        borderColor: COLORS.icon.outlineSecondary,
        borderRadius: 16,
        backgroundColor: COLORS.background.primary,
        ...SHADOWS.default,
      }}
    >
      <CText variant="containerLabel" bold numberOfLines={1}>
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
  );
};
