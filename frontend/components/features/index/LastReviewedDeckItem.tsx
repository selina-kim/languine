import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { useRouter } from "expo-router";
import { Pressable } from "react-native";

type LastReviewedDeckItemProps = {
  deckId: string;
  deckName: string;
  lastReviewed: string;
};

export const LastReviewedDeckItem = ({
  deckId,
  deckName,
  lastReviewed,
}: LastReviewedDeckItemProps) => {
  const router = useRouter();

  return (
    <Pressable
      onPress={() => {
        router.push({
          pathname: "/decks",
          params: { deckId },
        });
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
