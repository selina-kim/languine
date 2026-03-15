import { PlayIcon } from "@/assets/icons/PlayIcon";
import { CButton } from "@/components/common/CButton";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { View } from "react-native";

interface DeckPreviewCardProps {
  title: string;
  language: string;
  cardsDue: number;
  onReview: () => void;
}

export const DeckPreviewCard = ({
  title,
  language,
  cardsDue,
  onReview,
}: DeckPreviewCardProps) => {
  return (
    <View
      style={{
        padding: 20,
        borderColor: COLORS.text.primary,
        borderWidth: 2,
        borderRadius: 14,
        width: "100%",
        backgroundColor: COLORS.background.secondary,
      }}
    >
      <CText variant="deckPreviewTitle">{title}</CText>
      <CText variant="deckPreviewLanguage">{language}</CText>
      <CText variant="deckPreviewContent" style={{ marginVertical: 15 }}>
        {cardsDue} cards due
      </CText>
      <CButton
        onPress={onReview}
        variant="primary"
        label="Start Review"
        Icon={<PlayIcon stroke={COLORS.text.primary} />}
      />
    </View>
  );
};
