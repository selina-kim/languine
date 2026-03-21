import { getSingleDeck } from "@/apis/endpoints/decks";
import { EditIcon } from "@/assets/icons/EditIcon";
import { CButton } from "@/components/common/CButton";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { Card, DeckDetails } from "@/types/decks";
import { useEffect, useState } from "react";
import { Pressable, ScrollView, View } from "react-native";

interface SingleDeckViewProps {
  deck_id: string;
}

export const SingleDeckView = ({ deck_id }: SingleDeckViewProps) => {
  const [cards, setCards] = useState<Card[]>([]);
  const [deckDetails, setDeckDetails] = useState<DeckDetails>();

  useEffect(() => {
    const getDeck = async () => {
      const { data, error } = await getSingleDeck(deck_id);

      setCards(data.cards);
      setDeckDetails(data.deck);

      console.log(data);
      console.log("error", error);
    };

    getDeck();
  }, [deck_id]);

  const renderDeckDetails = () => {
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
          <DeckDetailItem label="Language" value={deckDetails.word_lang} />
          <DeckDetailItem
            label="Last Reviewed"
            value={deckDetails.last_reviewed}
          />
          <DeckDetailItem label="Total Cards" value={cards.length} />
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
          onPress={() => console.log("edit clicked")}
        >
          <EditIcon />
        </Pressable>
      </View>
    );
  };

  return (
    <View style={{ height: "100%" }}>
      <ScrollView
        contentContainerStyle={{
          display: "flex",
          justifyContent: "flex-start",
          alignItems: "flex-start",
          paddingHorizontal: 25,
          paddingVertical: 25,
          rowGap: 20,
        }}
      >
        {renderDeckDetails()}
        <CButton
          variant="primary"
          label="Export Deck"
          style={{ width: "100%", marginVertical: 10 }}
          onPress={() => console.log("export deck clicked")}
        />
        <CText variant="containerLabel">Flashcards ({cards.length})</CText>
      </ScrollView>
    </View>
  );
};
