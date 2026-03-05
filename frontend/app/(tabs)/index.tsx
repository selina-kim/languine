import { CText } from "@/components/common/CText";
import { RouteButton } from "@/components/common/RouteButton";
import { CardsDueBanner } from "@/components/features/index/CardsDueBanner";
import { LastReviewedDeckItem } from "@/components/features/index/LastReviewedDeckItem";
import { ScrollView, View } from "react-native";

// TODO: placeholder until we have real data
const sampleDecksList = [
  { name: "Korean Vocab", lastReviewed: new Date("2026-02-27") },
  { name: "French Vocab", lastReviewed: new Date("2026-02-22") },
  { name: "Japanese Vocab", lastReviewed: new Date("2026-02-24") },
  {
    name: "Really long title long long long long",
    lastReviewed: new Date("2026-02-24"),
  },
  {
    name: "Title 1",
    lastReviewed: new Date("2026-02-24"),
  },
  {
    name: "Title 2",
    lastReviewed: new Date("2026-02-24"),
  },
  {
    name: "Title 3",
    lastReviewed: new Date("2026-02-24"),
  },
];

export default function Index() {
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
        {sampleDecksList.map((deck) => (
          <LastReviewedDeckItem
            key={`last_reviewed_deck_card_${deck.name}`}
            deckName={deck.name}
            lastReviewed={deck.lastReviewed.toLocaleDateString()}
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
