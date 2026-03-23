import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { Pressable } from "react-native";

type LastReviewedDeckItemProps = {
  deckName: string;
  lastReviewed: string;
};

export const LastReviewedDeckItem = ({
  deckName,
  lastReviewed,
}: LastReviewedDeckItemProps) => {
  return (
    <Pressable
      onPress={() => {
        // TODO
        console.log(`${deckName} deck was clicked!`);
      }}
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
      <CText variant="containerLabel" numberOfLines={1}>
        {deckName}
      </CText>
      <CText
        style={{
          color: COLORS.text.secondary,
        }}
      >
        Last reviewed: {lastReviewed}
      </CText>
    </Pressable>
  );
};
