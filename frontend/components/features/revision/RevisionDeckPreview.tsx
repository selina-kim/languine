import { PlayIcon } from "@/assets/icons/PlayIcon";
import { CButton } from "@/components/common/CButton";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { View } from "react-native";

interface RevisionDeckPreviewProps {
  deckName: string;
  language: string;
  cardsDue: number;
  onReview: () => void;
}

export const RevisionDeckPreview = ({
  deckName,
  language,
  cardsDue,
  onReview,
}: RevisionDeckPreviewProps) => {
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
      <CText
        style={{
          fontSize: 22,
          lineHeight: 28,
        }}
        bold
      >
        {deckName}
      </CText>
      <CText
        style={{ color: COLORS.text.language, fontSize: 16, lineHeight: 24 }}
        special
      >
        {language}
      </CText>
      <CText
        style={{
          marginVertical: 15,
          color: COLORS.text.secondary,
          fontSize: 18,
          lineHeight: 24,
        }}
        bold
      >
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
