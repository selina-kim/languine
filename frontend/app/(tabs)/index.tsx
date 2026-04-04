import { getRecentDecks } from "@/apis/endpoints/decks";
import { getDueCards } from "@/apis/endpoints/fsrs";
import { CText } from "@/components/common/CText";
import { RouteButton } from "@/components/common/RouteButton";
import { CardsDueBanner } from "@/components/features/index/CardsDueBanner";
import { LastReviewedDeckItem } from "@/components/features/index/LastReviewedDeckItem";
import { Deck } from "@/types/decks";
import { useFocusEffect } from "@react-navigation/native";
import { useCallback, useState } from "react";
import { ScrollView, View } from "react-native";

export default function Index() {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [countDueCards, setCountDueCards] = useState<number>(0);

  useFocusEffect(
    useCallback(() => {
      const getHomeDecks = async () => {
        const { data, error } = await getRecentDecks(3);

        if (error) {
          console.log(error);
          return;
        }

        setDecks(data.decks);
      };

      const getDueCardsCount = async () => {
        const { data, error } = await getDueCards();

        if (error) {
          console.log(error);
          return;
        }

        setCountDueCards(data.num_due_cards);
      };

      getHomeDecks();
      getDueCardsCount();
    }, []),
  );

  const label = (
    <CText
      variant="title"
      style={{
        textAlign: "left",
        paddingHorizontal: 25,
        paddingTop: 25,
        paddingBottom: 5,
      }}
    >
      Last Reviewed Decks
    </CText>
  );
  return (
    <ScrollView
      style={{
        flex: 1,
        padding: 10,
      }}
    >
      <CardsDueBanner countDueCards={countDueCards} />
      {label}
      <View
        style={{
          display: "flex",
          marginHorizontal: 25,
          marginVertical: 10,
          rowGap: 20,
        }}
      >
        {decks.length > 0 ? (
          decks.map((deck) => (
            <LastReviewedDeckItem
              key={`last_reviewed_deck_card_${deck.d_id}`}
              deckId={deck.d_id}
              deckName={deck.deck_name}
              lastReviewed={new Date(deck.last_reviewed!).toLocaleDateString()}
            />
          ))
        ) : (
          <CText
            style={{
              textAlign: "center",
              top: 10,
            }}
          >
            No reviewed decks yet
          </CText>
        )}
      </View>
      <View
        style={{
          marginHorizontal: 50,
          marginVertical: 30,
        }}
      >
        <RouteButton text="View Decks" route="decks" />
      </View>
    </ScrollView>
  );
}
