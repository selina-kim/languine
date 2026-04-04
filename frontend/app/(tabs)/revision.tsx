import { getDecksWithDueCards } from "@/apis/endpoints/decks";
import { CText } from "@/components/common/CText";
import { RevisionDeckPreview } from "@/components/features/revision/RevisionDeckPreview";
import { SingleDeckReview } from "@/components/features/revision/SingleDeckReview";
import { COLORS } from "@/constants/colors";
import { useLanguageOptions } from "@/context/LanguageOptionsContext";
import { useReviewSession } from "@/context/ReviewSessionContext";
import { DueDeck } from "@/types/decks";
import { useFocusEffect } from "@react-navigation/native";
import { useLocalSearchParams, usePathname, useRouter } from "expo-router";
import { useCallback, useEffect, useState, useRef } from "react";
import { ActivityIndicator, ScrollView, View } from "react-native";

interface FocusedReviewDeck {
  d_id: string;
  deck_name: string;
}

export default function Revision() {
  const [decksList, setDecksList] = useState<DueDeck[]>([]);
  const [focusedDeck, setFocusedDeck] = useState<FocusedReviewDeck>();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>();
  const screenStart = useRef(Date.now());
  const hasMarked = useRef(false);
  const pathname = usePathname();
  const router = useRouter();
  const params = useLocalSearchParams<{ deckId?: string; deckName?: string }>();
  const routeDeckId =
    typeof params.deckId === "string" && params.deckId.trim().length > 0
      ? params.deckId
      : undefined;
  const routeDeckName =
    typeof params.deckName === "string" && params.deckName.trim().length > 0
      ? params.deckName
      : "Deck Review";
  const { getLanguageName } = useLanguageOptions();
  const {
    isReviewSessionActive,
    setIsReviewSessionActive,
    exitReviewSessionSignal,
  } = useReviewSession();

  const getDueDecks = useCallback(async () => {
    setIsLoading(true);
    setError(undefined);
    screenStart.current = Date.now();
    hasMarked.current = false;

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

  // Mark interactive once decks are loaded
  useEffect(() => {
    if (!isLoading && decksList.length > 0 && !hasMarked.current) {
      const tti = Date.now() - screenStart.current;
      console.log(`[PERF] RevisionScreen TTI: ${tti}ms`);
      hasMarked.current = true;
    }
  }, [isLoading, decksList]);

  useFocusEffect(
    useCallback(() => {
      getDueDecks();
    }, [getDueDecks]),
  );

  useEffect(() => {
    setFocusedDeck(undefined);
    setIsReviewSessionActive(false);
    getDueDecks();
  }, [exitReviewSessionSignal, getDueDecks, setIsReviewSessionActive]);

  useEffect(() => {
    if (!routeDeckId || focusedDeck) {
      return;
    }

    setFocusedDeck({
      d_id: routeDeckId,
      deck_name: routeDeckName,
    });
    setIsReviewSessionActive(true);
    router.replace("/(tabs)/revision");
  }, [
    focusedDeck,
    routeDeckId,
    routeDeckName,
    router,
    setIsReviewSessionActive,
  ]);

  useEffect(() => {
    if (pathname === "/revision" || isReviewSessionActive || !focusedDeck) {
      return;
    }

    setFocusedDeck(undefined);
    getDueDecks();
  }, [pathname, isReviewSessionActive, focusedDeck, getDueDecks]);

  const renderDecksList = () => (
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
      {isLoading && (
        <View style={{ paddingVertical: 16 }}>
          <ActivityIndicator size="large" color={COLORS.accent.primary} />
        </View>
      )}
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
          onReview={() => {
            setFocusedDeck({
              d_id: deck.d_id,
              deck_name: deck.deck_name,
            });
            setIsReviewSessionActive(true);
          }}
        />
      ))}
    </ScrollView>
  );

  return (
    <>
      <View style={{ height: "100%" }}>
        {focusedDeck ? (
          <SingleDeckReview
            deckId={focusedDeck.d_id}
            deckName={focusedDeck.deck_name}
            onReviewComplete={() => {
              setFocusedDeck(undefined);
              setIsReviewSessionActive(false);
              getDueDecks();
              router.push("/(tabs)/revision");
            }}
            onKeepStudying={() => {
              setFocusedDeck(undefined);
              setIsReviewSessionActive(false);
              getDueDecks();
              router.push("/(tabs)/revision");
            }}
            onGoHome={() => {
              setFocusedDeck(undefined);
              setIsReviewSessionActive(false);
              router.push("/(tabs)");
            }}
          />
        ) : (
          renderDecksList()
        )}
      </View>
    </>
  );
}
