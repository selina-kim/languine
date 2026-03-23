import { getDecks } from "@/apis/endpoints/decks";
import { CText } from "@/components/common/CText";
import { RouteButton } from "@/components/common/RouteButton";
import { CardsDueBanner } from "@/components/features/index/CardsDueBanner";
import { LastReviewedDeckItem } from "@/components/features/index/LastReviewedDeckItem";
import { Deck } from "@/types/decks";
import { useEffect, useState } from "react";
import { ScrollView, View } from "react-native";

export default function Index() {
  const [decks, setDecks] = useState<Deck[]>([]);

  useEffect(() => {
    const getHomeDecks = async () => {
      const { data, error } = await getDecks();

      if (error) {
        console.log(error);
        return;
      }

      // TODO: replace this with a dedicated "recent decks" endpoint when exposed in frontend API.
      setDecks(data.decks.slice(0, 3));
    };

    getHomeDecks();
  }, []);

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
      <CardsDueBanner countDueCards={5} />
      {label}
      <View
        style={{
          display: "flex",
          marginHorizontal: 25,
          marginVertical: 10,
          rowGap: 20,
        }}
      >
        {decks.map((deck) => (
          <LastReviewedDeckItem
            key={`last_reviewed_deck_card_${deck.d_id}`}
            deckName={deck.deck_name}
            lastReviewed={
              deck.last_reviewed
                ? new Date(deck.last_reviewed).toLocaleDateString()
                : "Never"
            }
          />
        ))}
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
