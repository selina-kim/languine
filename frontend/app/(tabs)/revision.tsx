import { CText } from "@/components/common/CText";
import { RevisionDeckPreview } from "@/components/features/revision/RevisionDeckPreview";
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
        justifyContent: "flex-start",
        alignItems: "center",
        paddingHorizontal: 25,
        paddingVertical: 25,
        rowGap: 20,
      }}
    >
      <CText variant="title">Select a deck to start your review session</CText>
      {decksList.map((deck) => (
        <RevisionDeckPreview
          key={`revision_deck_preview_${deck.title}`}
          deckName={deck.title}
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
