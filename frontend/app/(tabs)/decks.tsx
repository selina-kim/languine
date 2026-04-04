import { deleteDeck, getDecks } from "@/apis/endpoints/decks";
import { NoDecksBanner } from "@/components/features/decks/NoDecksBanner";
import { Pressable, ScrollView, View } from "react-native";
import { Deck } from "@/types/decks";
import { useEffect, useState, useRef, useCallback } from "react";
import { useFocusEffect } from "@react-navigation/native";
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
import { CreateOrImportDeckModal } from "@/components/features/decks/CreateOrImportDeckModal";
export default function Decks() {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [isCreateOrImportDeckModalOpen, setIsCreateOrImportDeckModalOpen] =
    useState(false);
  const [isCreateDeckModalOpen, setIsCreateDeckModalOpen] = useState(false);
  const [focusedDeckId, setFocusedDeckId] = useState<string>();
  const [deckIdToDelete, setDeckIdToDelete] = useState<string>();
  const [isDeletingDeck, setIsDeletingDeck] = useState(false);
  const [deleteDeckError, setDeleteDeckError] = useState<string>();
  const pathname = usePathname();
  const { getLanguageName } = useLanguageOptions();
  const screenStart = useRef(Date.now());
  const hasMarked = useRef(false);

  const getAllDecks = useCallback(async () => {
    const { data, error } = await getDecks();

    setDecks(data.decks);
    if (error) {
      console.log(error);
    }
  }, []);

  // Mark interactive once decks are loaded
  useEffect(() => {
    if (decks.length > 0 && !hasMarked.current) {
      const tti = Date.now() - screenStart.current;
      console.log(`[PERF] DecksScreen TTI: ${tti}ms`);
      hasMarked.current = true;
    }
  }, [decks]);

  useFocusEffect(
    useCallback(() => {
      screenStart.current = Date.now();
      hasMarked.current = false;
      setFocusedDeckId(undefined);
      getAllDecks();
    }, [getAllDecks]),
  );

  useEffect(() => {
    if (isCreateOrImportDeckModalOpen === false) {
      getAllDecks();
    }
  }, [isCreateOrImportDeckModalOpen, getAllDecks]);

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
        {deleteDeckError && (
          <CText variant="inputError">{deleteDeckError}</CText>
        )}
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
                setIsCreateOrImportDeckModalOpen(true);
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
        onPress={() => setIsCreateOrImportDeckModalOpen(true)}
      >
        <PlusFilledIcon />
      </Pressable>
      <CreateOrImportDeckModal
        isOpen={isCreateOrImportDeckModalOpen}
        onClose={() => setIsCreateOrImportDeckModalOpen(false)}
        onCreateDeck={() => setIsCreateDeckModalOpen(true)}
        onImportDeck={() => {}}
      />
      <CreateNewDeckModal
        isOpen={isCreateDeckModalOpen}
        onClose={() => setIsCreateDeckModalOpen(false)}
        onSuccess={() => {
          getAllDecks();
        }}
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
