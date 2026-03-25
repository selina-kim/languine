import { DeckDetails } from "@/types/decks";
import { COLORS } from "@/constants/colors";
import { Pressable, View } from "react-native";
import { SHADOWS } from "@/constants/shadows";
import { CText } from "@/components/common/CText";
import { EditIcon } from "@/assets/icons/EditIcon";
import { useLanguageOptions } from "@/context/LanguageOptionsContext";

export const SingleDeckDetails = ({
  deckDetails,
  numOfCards,
  onEditDeck,
}: {
  deckDetails: DeckDetails;
  numOfCards: number;
  onEditDeck: () => void;
}) => {
  const { getLanguageName } = useLanguageOptions();

  const DeckDetailItem = ({
    label,
    value,
  }: {
    label: string;
    value: string | number | null;
  }) => {
    return (
      <View style={{ width: "50%", marginBottom: 12 }}>
        <CText bold style={{ color: COLORS.text.secondary }}>
          {label}
        </CText>
        <CText>{value ?? "N/A"}</CText>
      </View>
    );
  };

  if (!deckDetails) {
    return;
  }

  return (
    <View
      style={{
        padding: 20,
        borderRadius: 14,
        width: "100%",
        backgroundColor: COLORS.background.secondary,
        ...SHADOWS.default,
      }}
    >
      <CText
        style={{
          fontSize: 22,
          lineHeight: 28,
        }}
        bold
      >
        {deckDetails.deck_name}
      </CText>
      <View
        style={{
          width: "100%",
          display: "flex",
          flexDirection: "row",
          flexWrap: "wrap",
          marginTop: 16,
        }}
      >
        <DeckDetailItem
          label="Language"
          value={getLanguageName(deckDetails.word_lang)}
        />
        <DeckDetailItem
          label="Last Reviewed"
          value={
            deckDetails.last_reviewed
              ? new Date(deckDetails.last_reviewed).toLocaleDateString()
              : "Never"
          }
        />
        <DeckDetailItem label="Total Cards" value={numOfCards} />
        <DeckDetailItem label="Cards Due" value="TODO" />
        <View>
          <CText bold style={{ color: COLORS.text.secondary }}>
            Description
          </CText>
          <CText>{deckDetails.description}</CText>
        </View>
      </View>
      <Pressable
        style={{
          width: 20,
          height: 20,
          position: "absolute",
          top: 20,
          right: 20,
        }}
        onPress={onEditDeck}
      >
        <EditIcon />
      </Pressable>
    </View>
  );
};
