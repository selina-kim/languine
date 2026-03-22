import { deleteDeck, getDecks } from "@/apis/endpoints/decks";
import { NoDecksBanner } from "@/components/features/decks/NoDecksBanner";
import { Pressable, ScrollView, View } from "react-native";
import { Deck } from "@/types/decks";
import { useEffect, useState } from "react";
import { DeckPreview } from "@/components/features/decks/DeckPreview";
import { PlusFilledIcon } from "@/assets/icons/PlusFilledIcon";
import { COLORS } from "@/constants/colors";
import { CreateNewDeckModal } from "@/components/features/decks/CreateNewDeckModal";
import { SHADOWS } from "@/constants/shadows";
import { useLanguageOptions } from "@/context/LanguageOptionsContext";
import { SingleDeckView } from "@/components/features/decks/SingleDeckView";
import { usePathname } from "expo-router";
import { Modal } from "@/components/common/Modal";
import { CText } from "@/components/common/CText";

export default function Decks() {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [isCreateDeckModalOpen, setIsCreateDeckModalOpen] = useState(false);
  const [focusedDeckId, setFocusedDeckId] = useState<string>();
  const [deckIdToDelete, setDeckIdToDelete] = useState<string>();
  const [isDeletingDeck, setIsDeletingDeck] = useState(false);
  const [deleteDeckError, setDeleteDeckError] = useState<string>();
  const pathname = usePathname();
  const { languageNameByCode } = useLanguageOptions();

  const getAllDecks = async () => {
    const { data, error } = await getDecks();

    setDecks(data.decks);
    if (error) {
      console.log(error);
    }
  };

  const getLanguageName = (code: string) =>
    languageNameByCode[code.toUpperCase()] ?? code.toUpperCase();

  useEffect(() => {
    setFocusedDeckId(undefined);
    getAllDecks();
  }, [isCreateDeckModalOpen, pathname]);

  const handleDeleteDeck = async (deckId: string) => {
    if (isDeletingDeck) {
      return;
    }

    setDeleteDeckError(undefined);
    setIsDeletingDeck(true);

    try {
      const { error } = await deleteDeck(deckId);

      if (error) {
        setDeleteDeckError(error);
        return;
      }

      setDecks((prevDecks) => prevDecks.filter((deck) => deck.d_id !== deckId));
      setDeckIdToDelete(undefined);
    } finally {
      setIsDeletingDeck(false);
    }
  };

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
        }}
      >
        {deleteDeckError && <CText variant="inputError">{deleteDeckError}</CText>}
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
                setIsCreateDeckModalOpen(true);
              }}
            />
          </View>
        ) : (
          decks.map((deck) => (
            <DeckPreview
              key={`deck_preview_card_${deck.d_id}`}
              deckName={deck.deck_name}
              language={getLanguageName(deck.word_lang)}
              description={deck.description}
              cardCount={deck.card_count}
              onViewDeck={() => setFocusedDeckId(deck.d_id)}
              onDeleteDeck={() => setDeckIdToDelete(deck.d_id)}
            />
          ))
        )}
      </ScrollView>
      <Pressable
        style={{
          right: 20,
          bottom: 20,
          position: "absolute",
          width: 60,
          height: 60,
          padding: 15,
          backgroundColor: COLORS.button.fillPrimary,
          borderRadius: 10,
          ...SHADOWS.smallButton,
        }}
        onPress={() => setIsCreateDeckModalOpen(true)}
      >
        <PlusFilledIcon />
      </Pressable>
      <CreateNewDeckModal
        isOpen={isCreateDeckModalOpen}
        onClose={() => setIsCreateDeckModalOpen(false)}
      />
      {deckIdToDelete && (
        <Modal
          visible={!!deckIdToDelete}
          header="Are you sure?"
          submitLabel="Delete Deck"
          subheader="This action will delete this deck permanently"
          submitVariant="criticalPrimary"
          closeLabel="Cancel"
          isLoading={isDeletingDeck}
          onClose={() => setDeckIdToDelete(undefined)}
          onSubmit={() => handleDeleteDeck(deckIdToDelete)}
        />
      )}
    </>
  );

  return (
    <View style={{ height: "100%" }}>
      {focusedDeckId ? (
        <SingleDeckView deckId={focusedDeckId} />
      ) : (
        renderDecksView()
      )}
    </View>
  );
}
