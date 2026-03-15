import { CText } from "@/components/common/CText";
import { DeckPreviewCard } from "@/components/features/revision/DeckPreviewCard";
import { ScrollView } from "react-native";

export default function Revision() {
  const decksList = [
    { title: "Korean Deck", language: "KOREAN", cardsDue: 2 },
    { title: "French Deck", language: "FRENCH", cardsDue: 5 },
    { title: "Sample Deck 1", language: "FRENCH", cardsDue: 3 },
    { title: "Sample Deck 2", language: "FRENCH", cardsDue: 4 },
  ];
  return (
    <ScrollView
      contentContainerStyle={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        paddingHorizontal: 25,
        paddingVertical: 25,
        rowGap: 20,
      }}
    >
      <CText variant="title">Select a deck to start your review session</CText>
      {decksList.map((deck) => (
        <DeckPreviewCard
          key={`deck_preview_card_${deck.title}`}
          title={deck.title}
          language={deck.language}
          cardsDue={deck.cardsDue}
          onReview={() =>
            console.log(`review clicked for the deck ${deck.title}`)
          }
        />
      ))}
    </ScrollView>
  );
}
