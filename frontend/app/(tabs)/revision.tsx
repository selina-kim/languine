import { getDecksWithDueCards } from "@/apis/endpoints/decks";
import { CText } from "@/components/common/CText";
import { RevisionDeckPreview } from "@/components/features/revision/RevisionDeckPreview";
import { useLanguageOptions } from "@/context/LanguageOptionsContext";
import { DueDeck } from "@/types/decks";
import { useFocusEffect } from "@react-navigation/native";
import { useCallback, useState } from "react";
import { ScrollView } from "react-native";

export default function Revision() {
  const [decksList, setDecksList] = useState<DueDeck[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>();
  const { getLanguageName } = useLanguageOptions();

  const getDueDecks = useCallback(async () => {
    setIsLoading(true);
    setError(undefined);

    try {
      const { data, error: responseError } = await getDecksWithDueCards(20);

      if (responseError) {
        setError(responseError);
        return;
      }

      setDecksList(data.decks);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      getDueDecks();
    }, [getDueDecks]),
  );

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
      {isLoading && <CText>Loading decks...</CText>}
      {error && <CText variant="inputError">{error}</CText>}
      {!isLoading && !error && decksList.length === 0 && (
        <CText>No decks with due cards right now.</CText>
      )}
      {decksList.map((deck) => (
        <RevisionDeckPreview
          key={`revision_deck_preview_${deck.d_id}`}
          deckName={deck.deck_name}
          language={getLanguageName(deck.word_lang)}
          cardsDue={deck.due_count}
          onReview={() =>
            console.log(`review clicked for the deck ${deck.deck_name}`)
          }
        />
      ))}
    </ScrollView>
  );
}
