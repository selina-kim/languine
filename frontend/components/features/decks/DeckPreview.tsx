import { TrashIcon } from "@/assets/icons/TrashIcon";
import { CButton } from "@/components/common/CButton";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { Pressable, View } from "react-native";

interface DeckPreviewProps {
  deckName: string;
  description?: string;
  language: string;
  cardCount: number;
  onViewDeck: () => void;
  onDeleteDeck: () => void;
}

export const DeckPreview = ({
  deckName,
  description,
  language,
  cardCount,
  onViewDeck,
  onDeleteDeck,
}: DeckPreviewProps) => {
  const hasDescription = description && description.trim() !== "";

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
        {language.toUpperCase()}
      </CText>
      {hasDescription && (
        <CText
          numberOfLines={2}
          style={{
            marginTop: 15,
          }}
        >
          {description}
        </CText>
      )}
      <CText
        style={{
          marginTop: 15,
          marginBottom: 15,
        }}
      >
        {cardCount} cards
      </CText>
      <CButton onPress={onViewDeck} variant="primary" label="View Deck" />
      <Pressable
        style={{
          width: 20,
          height: 20,
          position: "absolute",
          top: 20,
          right: 20,
        }}
        onPress={onDeleteDeck}
      >
        <TrashIcon />
      </Pressable>
    </View>
  );
};
