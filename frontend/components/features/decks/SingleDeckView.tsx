import { getSingleDeck } from "@/apis/endpoints/decks";
import { PlusIcon } from "@/assets/icons/PlusIcon";
import { CButton } from "@/components/common/CButton";
import { Modal } from "@/components/common/Modal";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { SHADOWS } from "@/constants/shadows";
import { Card, DeckDetails } from "@/types/decks";
import { useEffect, useState } from "react";
import { Pressable, ScrollView, View } from "react-native";
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
  const router = useRouter();
  const [cards, setCards] = useState<Card[]>([]);
  const [deckDetails, setDeckDetails] = useState<DeckDetails>();
  const [isStartReviewModalVisible, setIsStartReviewModalVisible] =
    useState(false);
  const [isCreateCardModalOpen, setIsCreateCardModalOpen] = useState(false);
  const [isEditDeckModalOpen, setIsEditDeckModalOpen] = useState(false);
  const [isEditCardModalOpen, setIsEditCardModalOpen] = useState(false);
  const [cardBeingEdited, setCardBeingEdited] = useState<Card | null>(null);

  useEffect(() => {
    const getDeck = async () => {
      const { data, error } = await getSingleDeck(deckId);

      setCards(data.cards);
      setDeckDetails(data.deck);

      if (error) {
        console.log(error);
      }
    };

    getDeck();
  }, [deckId]);

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

  if (!deckDetails) {
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
          numOfCards={cards.length}
          onEditDeck={() => setIsEditDeckModalOpen(true)}
        />
        <CButton
          variant="primary"
          label="Export Deck"
          style={{ width: "100%", marginVertical: 10 }}
          onPress={() => console.log("export deck clicked")}
        />
        <CText variant="containerLabel">Flashcards ({cards.length})</CText>
        {cards.length === 0 ? (
          renderNoCardsBanner()
        ) : (
          <CardsList
            deckId={deckId}
            cards={cards}
            onCardDeleted={(cardId) =>
              setCards((prevCards) =>
                prevCards.filter((card) => card.c_id !== cardId),
              )
            }
            onCardEdit={(card) => {
              setCardBeingEdited(card);
              setIsEditCardModalOpen(true);
            }}
          />
        )}
      </ScrollView>
      {cards.length !== 0 && (
        <View style={{right: 20,
            bottom: 20,
            position: "absolute",
            display: "flex", rowGap: 10}}>
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
          <OpenBookIcon strokeWidth={3}/>
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
        onOptimisticCreate={(optimisticCard) =>
          setCards((prevCards) => [optimisticCard, ...prevCards])
        }
        onCreateSuccess={(tempCardId, createdCard) =>
          setCards((prevCards) =>
            prevCards.map((card) =>
              card.c_id === tempCardId ? createdCard : card,
            ),
          )
        }
        onCreateFailed={(tempCardId) =>
          setCards((prevCards) =>
            prevCards.filter((card) => card.c_id !== tempCardId),
          )
        }
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
