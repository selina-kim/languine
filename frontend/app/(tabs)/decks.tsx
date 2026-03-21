import { getDecks } from "@/apis/endpoints/decks";
import { NoDecksBanner } from "@/components/features/decks/NoDecksBanner";
import { Pressable, ScrollView, View } from "react-native";
import { Deck } from "@/types/decks";
import { useEffect, useState } from "react";
import { DeckPreview } from "@/components/features/decks/DeckPreview";
import { PlusFilledIcon } from "@/assets/icons/PlusFilledIcon";
import { COLORS } from "@/constants/colors";
import { CreateNewDeckModal } from "@/components/features/decks/CreateNewDeckModal";
import { SHADOWS } from "@/constants/shadows";
import { SingleDeckView } from "@/components/features/decks/SingleDeckView";
import { usePathname } from "expo-router";

export default function Decks() {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [focusedDeckId, setFocusedDeckId] = useState<string>();
  const pathname = usePathname();

  const getAllDecks = async () => {
    const { data, error } = await getDecks();

    setDecks(data.decks);

    console.log("error", error);
  };

  useEffect(() => {
    setFocusedDeckId(undefined);
    getAllDecks();
  }, [isModalOpen, pathname]);

  const renderDecksView = () => (
    <>
      <ScrollView
        contentContainerStyle={{
          display: "flex",
          justifyContent: "flex-start",
          alignItems: "center",
          paddingHorizontal: 25,
          paddingVertical: 25,
          rowGap: 20,
          borderColor: "red",
        }}
      >
        {decks.length === 0 ? (
          <View
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              padding: 10,
            }}
          >
            <NoDecksBanner
              onCreateNewDeck={() => {
                setIsModalOpen(true);
              }}
            />
          </View>
        ) : (
          decks.map((deck) => (
            <DeckPreview
              key={`deck_preview_card_${deck.deck_name}`}
              deckName={deck.deck_name}
              language={deck.word_lang}
              description={deck.description}
              cardCount={deck.card_count}
              onViewDeck={() => setFocusedDeckId(deck.d_id)}
              onDeleteDeck={() =>
                console.log(`clicked delete deck for ${deck.deck_name}`)
              }
            />
          ))
        )}
      </ScrollView>
      <Pressable
        style={{
          right: 10,
          bottom: 10,
          position: "absolute",
          width: 60,
          height: 60,
          padding: 15,
          backgroundColor: COLORS.button.fillPrimary,
          borderRadius: 10,
          ...SHADOWS.smallButton,
        }}
        onPress={() => setIsModalOpen(true)}
      >
        <PlusFilledIcon />
      </Pressable>
      <CreateNewDeckModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );

  return (
    <View style={{ height: "100%" }}>
      {focusedDeckId ? (
        <SingleDeckView deck_id={focusedDeckId} />
      ) : (
        renderDecksView()
      )}
    </View>
  );
}
