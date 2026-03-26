import { getReviewCards } from "@/apis/endpoints/cards";
import { logReview, endReview } from "@/apis/endpoints/fsrs";
import { HomeIcon } from "@/assets/icons/HomeIcon";
import { RepeatIcon } from "@/assets/icons/RepeatIcon";
import { SoundIcon } from "@/assets/icons/SoundIcon";
import { CButton } from "@/components/common/CButton";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { useReviewSession } from "@/context/ReviewSessionContext";
import { Card } from "@/types/decks";
import { getImageUrl } from "@/utils/imageUtils";
import { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, Image, Pressable, ScrollView, View } from "react-native";

interface SingleDeckReviewProps {
  deckId: string;
  deckName: string;
  onGoHome: () => void;
  onReviewComplete: () => void;
  onKeepStudying: () => void;
}

export const SingleDeckReview = ({
  deckId,
  deckName,
  onGoHome,
  onReviewComplete,
  onKeepStudying,
}: SingleDeckReviewProps) => {
  const [cards, setCards] = useState<Card[]>([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFrontSide, setIsFrontSide] = useState(true);
  const [hasRevealedBackOnce, setHasRevealedBackOnce] = useState(false);
  const [isReviewComplete, setIsReviewComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>();
  const cardStartTimeRef = useRef<number | null>(null);
  const { exitReviewSessionSignal } = useReviewSession();

  const difficultyOptions = [
    { label: "Again", borderColor: "#F2A5A1", grade: 1 },
    { label: "Hard",  borderColor: "#F1B35E", grade: 2 },
    { label: "Good",  borderColor: "#ADD85D", grade: 3 },
    { label: "Easy",  borderColor: "#7CD6A0", grade: 4 },
  ];

  const getCardsToReview = useCallback(async () => {
    setIsLoading(true);
    setError(undefined);

    try {
      const { data, error: responseError } = await getReviewCards(deckId, 50);

      if (responseError) {
        setError(responseError);
        return;
      }

      setCards(data.cards);
      setCurrentCardIndex(0);
      setIsFrontSide(true);
      setHasRevealedBackOnce(false);
      setIsReviewComplete(false);
      cardStartTimeRef.current = Date.now();
    } finally {
      setIsLoading(false);
    }
  }, [deckId]);

  useEffect(() => {
    getCardsToReview();
  }, [getCardsToReview]);

  // Call endReview when session is exited (e.g., back gesture or app close)
  useEffect(() => {
    if (exitReviewSessionSignal > 0 && currentCardIndex > 0 && !isReviewComplete) {
      endReview(currentCardIndex);
    }
  }, [exitReviewSessionSignal, currentCardIndex, isReviewComplete]);

  const totalCards = cards.length;
  const currentCard = cards[currentCardIndex];
  const progress = totalCards === 0 ? 0 : (currentCardIndex + 1) / totalCards;

  const handleCardPress = () => {
    if (isFrontSide) {
      setIsFrontSide(false);
      setHasRevealedBackOnce(true);
      return;
    }

    setIsFrontSide(true);
  };

  const handleSelectDifficulty = async (grade: number) => {
    // Calculate review duration
    const reviewDuration = cardStartTimeRef.current
      ? Date.now() - cardStartTimeRef.current
      : 0;

    // Log the review to backend
    if (currentCard) {
      const { error: reviewError } = await logReview(
        currentCard.c_id,
        grade,
        reviewDuration,
      );
      if (reviewError) {
        console.error("Failed to log review:", reviewError);
      }
    }

    if (currentCardIndex >= totalCards - 1) {
      // Session complete - call end-review to update deck due counts
      const { error: endReviewError } = await endReview(totalCards);
      if (endReviewError) {
        console.error("Failed to end review session:", endReviewError);
      }

      setIsReviewComplete(true);
      return;
    }

    // Reset timer and move to next card
    cardStartTimeRef.current = Date.now();
    setCurrentCardIndex((prev) => prev + 1);
    setIsFrontSide(true);
    setHasRevealedBackOnce(false);
  };

  const handleKeepStudying = () => {
    onReviewComplete();
    onKeepStudying();
  };

  const handleGoHome = () => {
    onReviewComplete();
    onGoHome();
  };

  return (
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
      <CText bold style={{ fontSize: 22 }}>
        {deckName}
      </CText>

      {isLoading && (
        <View style={{ paddingVertical: 16, marginHorizontal: "auto" }}>
          <ActivityIndicator size="large" color={COLORS.accent.primary} />
        </View>
      )}
      {error && <CText variant="inputError">{error}</CText>}
      {!isLoading && !error && cards.length === 0 && (
        <CText>No cards are due right now.</CText>
      )}

      {!isLoading && !error && isReviewComplete && (
        <View
          style={{
            width: "100%",
            alignItems: "center",
            justifyContent: "center",
            marginTop: 60,
            rowGap: 18,
            paddingHorizontal: 8,
          }}
        >
          <CText
            bold
            style={{
              fontSize: 34,
              lineHeight: 40,
              textAlign: "center",
            }}
          >
            Review Complete! 🎉
          </CText>
          <CText
            style={{
              textAlign: "center",
              color: COLORS.text.secondary,
              fontSize: 18,
              lineHeight: 28,
            }}
          >
            You reviewed {totalCards} cards in this session.
          </CText>

          <View
            style={{
              width: "100%",
              display: "flex",
              flexDirection: "row",
              justifyContent: "center",
              columnGap: 10,
              marginTop: 8,
            }}
          >
            <CButton
              variant="primary"
              label="Keep Studying"
              onPress={handleKeepStudying}
              Icon={<RepeatIcon />}
            />
            <CButton
              variant="secondary"
              label="Go Home"
              onPress={handleGoHome}
              Icon={<HomeIcon strokeWidth={3.2} stroke={COLORS.text.primary} />}
            />
          </View>
        </View>
      )}

      {!isLoading && !error && !isReviewComplete && currentCard && (
        <>
          <View style={{ width: "100%", rowGap: 6 }}>
            <CText bold>
              Card {currentCardIndex + 1} of {totalCards}
            </CText>
            <View
              style={{
                width: "100%",
                height: 8,
                borderRadius: 8,
                overflow: "hidden",
              }}
            >
              <View
                style={{
                  width: "100%",
                  height: 8,
                  borderRadius: 8,
                  backgroundColor: COLORS.text.secondary,
                  opacity: 0.5,
                  overflow: "hidden",
                }}
              />
              <View
                style={{
                  position: "absolute",
                  width: `${progress * 100}%`,
                  height: "100%",
                  backgroundColor: COLORS.text.primary,
                }}
              />
            </View>
          </View>
          <Pressable onPress={handleCardPress} style={{ width: "100%" }}>
            <View
              style={{
                padding: 20,
                borderRadius: 14,
                borderColor: COLORS.icon.outlinePrimary,
                borderWidth: 2,
                width: "100%",
                backgroundColor: isFrontSide ? COLORS.background.primary : COLORS.background.secondary,
                rowGap: 14,
                position: "relative",
              }}
            >
              <Pressable
                style={{
                  position: "absolute",
                  top: 10,
                  left: 10,
                  zIndex: 10,
                  padding: 8,
                }}
                onPress={() =>
                  console.log(`TTS clicked for card ${currentCard.word}`)
                }
              >
                <SoundIcon />
              </Pressable>
              <CText
                style={{
                  textAlign: "center",
                  fontSize: 36,
                  lineHeight: 44,
                }}
                bold
              >
                {isFrontSide ? currentCard.word : currentCard.translation}
              </CText>

              {currentCard.image && (
                <View
                  style={{
                    height: 220,
                    width: "100%",
                    overflow: "hidden",
                    borderRadius: 8,
                  }}
                >
                  <Image
                    source={{
                      uri: getImageUrl(currentCard.image) ?? currentCard.image,
                    }}
                    style={{ height: "100%", width: "100%" }}
                    resizeMode="cover"
                  />
                </View>
              )}

              {isFrontSide && currentCard.word_example && (
                <CText style={{ textAlign: "center" }}>
                  {currentCard.word_example}
                </CText>
              )}

              {!isFrontSide && currentCard.trans_example && (
                <CText style={{ textAlign: "center" }}>
                  {currentCard.trans_example}
                </CText>
              )}
              <CText
                style={{
                  textAlign: "center",
                  color: COLORS.text.secondary,
                }}
              >
                {isFrontSide ? "(Front)\n" : "(Back)\n"} Tap to flip card
              </CText>
            </View>
          </Pressable>

          {hasRevealedBackOnce && (
            <View
              style={{
                width: "100%",
                display: "flex",
                flexDirection: "row",
                justifyContent: "space-between",
              }}
            >
              {difficultyOptions.map((option) => (
                <Pressable
                  key={option.label}
                  onPress={() => handleSelectDifficulty(option.grade)}
                  style={{
                    width: "23%",
                    borderWidth: 2,
                    borderColor: option.borderColor,
                    borderRadius: 12,
                    paddingVertical: 10,
                    alignItems: "center",
                    justifyContent: "center",
                    rowGap: 4,
                    backgroundColor: COLORS.background.primary,
                    height: 80,
                  }}
                >
                  <CText style={{ fontSize: 18, lineHeight: 24 }}>
                    {option.label}
                  </CText>
                </Pressable>
              ))}
            </View>
          )}
        </>
      )}
    </ScrollView>
  );
};
