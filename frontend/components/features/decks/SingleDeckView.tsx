import { getCards } from "@/apis/endpoints/cards";
import { exportDeck, getDecks } from "@/apis/endpoints/decks";
import { PlusIcon } from "@/assets/icons/PlusIcon";
import { CButton } from "@/components/common/CButton";
import { Modal } from "@/components/common/Modal";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { Card, DeckDetails } from "@/types/decks";
import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  View,
  Platform,
} from "react-native";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { CreateNewCardModal } from "./CreateNewCardModal";
import { PlusFilledIcon } from "@/assets/icons/PlusFilledIcon";
import { CardsList } from "./CardsList";
import { SingleDeckDetails } from "./SingleDeckDetails";
import { CreateNewDeckModal } from "./CreateNewDeckModal";
import { OpenBookIcon } from "@/assets/icons/OpenBookIcon";
import { useRouter } from "expo-router";

interface SingleDeckViewProps {
  deckId: string;
}

export const SingleDeckView = ({ deckId }: SingleDeckViewProps) => {
  const CARDS_PER_PAGE = 100;
  const router = useRouter();
  const [cards, setCards] = useState<Card[]>([]);
  const [totalCards, setTotalCards] = useState(0);
  const [nextPage, setNextPage] = useState(1);
  const [hasMoreCards, setHasMoreCards] = useState(false);
  const [isLoadingCards, setIsLoadingCards] = useState(false);
  const [isLoadingDeckDetails, setIsLoadingDeckDetails] = useState(false);
  const [isLoadingMoreCards, setIsLoadingMoreCards] = useState(false);
  const [deckDetails, setDeckDetails] = useState<DeckDetails>();
  const [isStartReviewModalVisible, setIsStartReviewModalVisible] =
    useState(false);
  const [isCreateCardModalOpen, setIsCreateCardModalOpen] = useState(false);
  const [isEditDeckModalOpen, setIsEditDeckModalOpen] = useState(false);
  const [isEditCardModalOpen, setIsEditCardModalOpen] = useState(false);
  const [cardBeingEdited, setCardBeingEdited] = useState<Card | null>(null);
  const [isExportingDeck, setIsExportingDeck] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const loadDeckView = async () => {
      setIsLoadingDeckDetails(true);
      setIsLoadingCards(true);

      const decksPromise = getDecks();
      const cardsPromise = getCards(deckId, 1, CARDS_PER_PAGE);

      const decksResponse = await decksPromise;

      if (isMounted) {
        if (decksResponse.error) {
          console.log(decksResponse.error);
        } else {
          const deck = decksResponse.data.decks.find(
            (candidateDeck) => String(candidateDeck.d_id) === String(deckId),
          );

          if (deck) {
            setDeckDetails({
              d_id: Number(deck.d_id),
              deck_name: deck.deck_name,
              word_lang: deck.word_lang,
              trans_lang: deck.trans_lang,
              description: deck.description,
              creation_date: deck.creation_date,
              last_reviewed: deck.last_reviewed,
              is_public: deck.is_public,
            });
          }
        }

        setIsLoadingDeckDetails(false);
      }

      const cardsResponse = await cardsPromise;

      if (isMounted) {
        if (cardsResponse.error) {
          console.log(cardsResponse.error);
        } else {
          setCards(cardsResponse.data.cards);
          setTotalCards(cardsResponse.data.pagination.total);
          setNextPage(cardsResponse.data.pagination.page + 1);
          setHasMoreCards(
            cardsResponse.data.pagination.page <
              cardsResponse.data.pagination.total_pages,
          );
        }

        setIsLoadingCards(false);
      }
    };

    loadDeckView();

    return () => {
      isMounted = false;
    };
  }, [deckId]);

  const loadMoreCards = async () => {
    if (!hasMoreCards || isLoadingMoreCards) {
      return;
    }

    setIsLoadingMoreCards(true);

    const { data, error } = await getCards(deckId, nextPage, CARDS_PER_PAGE);

    if (error) {
      console.log(error);
      setIsLoadingMoreCards(false);
      return;
    }

    setCards((prevCards) => [...prevCards, ...data.cards]);
    setTotalCards(data.pagination.total);
    setNextPage(data.pagination.page + 1);
    setHasMoreCards(data.pagination.page < data.pagination.total_pages);
    setIsLoadingMoreCards(false);
  };

  const handleExportDeck = async () => {
    if (isExportingDeck) {
      return;
    }

    setIsExportingDeck(true);
    try {
      const response = await exportDeck(deckId, "json");

      const disposition = response.headers.get("Content-Disposition") || "";
      let filename = `${deckDetails?.deck_name ?? "deck"}.json`;
      const match = disposition.match(/filename="?([^";]+)"?/i);
      if (match && match[1]) {
        filename = match[1];
      }

      if (Platform.OS === "web") {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        Alert.alert("Deck exported", "Your deck file has been downloaded.");
      } else {
        const content = await response.text();

        if (Platform.OS === "android") {
          const permissions =
            await FileSystem.StorageAccessFramework.requestDirectoryPermissionsAsync();

          if (!permissions.granted || !permissions.directoryUri) {
            Alert.alert(
              "Export canceled",
              "No folder selected, so the deck was not exported.",
            );
            return;
          }

          const safeFilename = filename.replace(/[\\/:*?"<>|]/g, "_");
          const fileUri =
            await FileSystem.StorageAccessFramework.createFileAsync(
              permissions.directoryUri,
              safeFilename,
              "application/json",
            );

          await FileSystem.writeAsStringAsync(fileUri, content, {
            encoding: FileSystem.EncodingType.UTF8,
          });

          Alert.alert(
            "Deck exported",
            "Your deck file has been saved to the selected folder.",
          );
          return;
        }

        const baseDir =
          (FileSystem.cacheDirectory as string | undefined) ??
          (FileSystem.documentDirectory as string | undefined) ??
          "";
        const fileUri = `${baseDir}${filename}`;
        await FileSystem.writeAsStringAsync(fileUri, content);

        if (await Sharing.isAvailableAsync()) {
          await Sharing.shareAsync(fileUri, {
            mimeType: "application/json",
            UTI: "public.json",
            dialogTitle: "Save or share your exported deck",
          });
        }

        Alert.alert(
          "Deck exported",
          "Your deck file is ready. Choose Save to Files in the share menu.",
        );
        return;
      }
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to export deck.";
      console.log(message);
      Alert.alert("Export failed", message);
    } finally {
      setIsExportingDeck(false);
    }
  };

  const renderNoCardsBanner = () => (
    <View
      style={{
        width: "100%",
        borderColor: "#d5d5d5",
        borderWidth: 1,
        padding: 30,
        borderRadius: 14,
      }}
    >
      <CText
        style={{
          color: COLORS.text.secondary,
          textAlign: "center",
        }}
      >
        This deck doesn&apos;t have any cards yet.
      </CText>
      <CButton
        variant="primary"
        label="Add Card"
        Icon={<PlusIcon />}
        style={{ marginHorizontal: "auto", marginTop: 15 }}
        onPress={() => setIsCreateCardModalOpen(true)}
      />
    </View>
  );

  const cardsDue = useMemo(() => {
    const now = new Date();
    const DAILY_NEW_LIMIT = 10; // Max new cards per day (independent limit)

    // Separate new cards (learning_state = 0) from reviewed cards
    const newCards = cards.filter((card) => card.learning_state === 0);
    const reviewedCards = cards.filter((card) => card.learning_state > 0);

    // Count reviewed cards that are due
    const reviewedCardsDue = reviewedCards.filter((card) => {
      if (!card.due_date) return false;
      return new Date(card.due_date) <= now;
    }).length;

    // New cards: up to 10 per day (independent limit, not affected by reviewed cards)
    const newCardsDue = Math.min(newCards.length, DAILY_NEW_LIMIT);

    // Total: new (capped at 10) + all reviewed that are due (no cap)
    return newCardsDue + reviewedCardsDue;
  }, [cards]);

  if (!deckDetails) {
    if (isLoadingDeckDetails) {
      return (
        <View style={{ padding: 25, marginHorizontal: "auto" }}>
          <ActivityIndicator size="large" color={COLORS.accent.primary} />
        </View>
      );
    }

    return;
  }

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
        <SingleDeckDetails
          deckDetails={deckDetails}
          numOfCards={totalCards}
          cardsDue={cardsDue}
          onEditDeck={() => setIsEditDeckModalOpen(true)}
        />
        <CButton
          variant="primary"
          label={isExportingDeck ? "Exporting..." : "Export Deck"}
          style={{ width: "100%", marginVertical: 10 }}
          disabled={isExportingDeck}
          onPress={handleExportDeck}
        />
        <CText variant="containerLabel">Flashcards ({totalCards})</CText>
        {isLoadingCards ? (
          <View
            style={{
              width: "100%",
              alignItems: "center",
              justifyContent: "center",
              paddingVertical: 20,
            }}
          >
            <ActivityIndicator size="large" color={COLORS.accent.primary} />
          </View>
        ) : totalCards === 0 ? (
          renderNoCardsBanner()
        ) : (
          <>
            <CardsList
              deckId={deckId}
              cards={cards}
              onCardDeleted={(cardId) => {
                setCards((prevCards) =>
                  prevCards.filter((card) => card.c_id !== cardId),
                );
                setTotalCards((prevTotal) => Math.max(prevTotal - 1, 0));
              }}
              onCardEdit={(card) => {
                setCardBeingEdited(card);
                setIsEditCardModalOpen(true);
              }}
            />
            {hasMoreCards && (
              <CButton
                variant="secondary"
                label={isLoadingMoreCards ? "Loading..." : "Load 100 more"}
                disabled={isLoadingMoreCards}
                style={{ width: "100%" }}
                onPress={loadMoreCards}
              />
            )}
          </>
        )}
      </ScrollView>
      {totalCards !== 0 && (
        <View
          style={{
            right: 20,
            bottom: 20,
            position: "absolute",
            display: "flex",
            rowGap: 10,
          }}
        >
          <Pressable
            style={{
              width: 60,
              height: 60,
              padding: 15,
              backgroundColor: COLORS.button.fillPrimary,
              borderRadius: 10,
              ...SHADOWS.smallButton,
            }}
            onPress={() => setIsStartReviewModalVisible(true)}
          >
            <OpenBookIcon strokeWidth={3} />
          </Pressable>
          <Pressable
            style={{
              width: 60,
              height: 60,
              padding: 15,
              backgroundColor: COLORS.button.fillPrimary,
              borderRadius: 10,
              ...SHADOWS.smallButton,
            }}
            onPress={() => setIsCreateCardModalOpen(true)}
          >
            <PlusFilledIcon />
          </Pressable>
        </View>
      )}
      <CreateNewCardModal
        deckId={deckId}
        wordLanguageCode={deckDetails.word_lang}
        translationLanguageCode={deckDetails.trans_lang}
        isOpen={isCreateCardModalOpen}
        onOptimisticCreate={(optimisticCard) => {
          setCards((prevCards) => [optimisticCard, ...prevCards]);
          setTotalCards((prevTotal) => prevTotal + 1);
        }}
        onCreateSuccess={(tempCardId, createdCard) => {
          setCards((prevCards) =>
            prevCards.map((card) =>
              card.c_id === tempCardId ? createdCard : card,
            ),
          );
        }}
        onCreateFailed={(tempCardId) => {
          setCards((prevCards) =>
            prevCards.filter((card) => card.c_id !== tempCardId),
          );
          setTotalCards((prevTotal) => Math.max(prevTotal - 1, 0));
        }}
        onClose={() => setIsCreateCardModalOpen(false)}
      />
      <CreateNewDeckModal
        isOpen={isEditDeckModalOpen}
        onClose={() => setIsEditDeckModalOpen(false)}
        mode="edit"
        deckToEdit={deckDetails}
        onSuccess={(updatedDeck) => {
          if (!updatedDeck) {
            return;
          }

          setDeckDetails((prevDeck) =>
            prevDeck
              ? {
                  ...prevDeck,
                  ...updatedDeck,
                }
              : prevDeck,
          );
        }}
      />
      {cardBeingEdited && (
        <CreateNewCardModal
          mode="edit"
          deckId={deckId}
          card={cardBeingEdited}
          wordLanguageCode={deckDetails.word_lang}
          translationLanguageCode={deckDetails.trans_lang}
          isOpen={isEditCardModalOpen}
          onUpdateSuccess={(updatedCard) => {
            setCards((prevCards) =>
              prevCards.map((card) =>
                card.c_id === updatedCard.c_id ? updatedCard : card,
              ),
            );
            setIsEditCardModalOpen(false);
          }}
          onUpdateFailed={() => {
            setIsEditCardModalOpen(false);
          }}
          onClose={() => {
            setIsEditCardModalOpen(false);
            setCardBeingEdited(null);
          }}
        />
      )}
      <Modal
        visible={isStartReviewModalVisible}
        header="Are you sure?"
        subheader="This will start the review session for this deck"
        submitLabel="Start Review"
        closeLabel="Cancel"
        onSubmit={() => {
          setIsStartReviewModalVisible(false);
          router.push({
            pathname: "/(tabs)/revision",
            params: {
              deckId,
              deckName: deckDetails.deck_name,
            },
          });
        }}
        onClose={() => setIsStartReviewModalVisible(false)}
      />
    </View>
  );
};
