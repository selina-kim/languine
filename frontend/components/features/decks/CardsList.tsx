import { EditIcon } from "@/assets/icons/EditIcon";
import { TrashIcon } from "@/assets/icons/TrashIcon";
import { deleteCard } from "@/apis/endpoints/cards";
import { CText } from "@/components/common/CText";
import { COLORS } from "@/constants/colors";
import { Card } from "@/types/decks";
import { useState } from "react";
import { Image, Pressable, View } from "react-native";
import { Modal } from "@/components/common/Modal";
import { getImageUrl } from "@/utils/imageUtils";

interface CardsListProps {
  deckId: string;
  cards: Card[];
  onCardDeleted: (cardId: number) => void;
  onCardEdit: (card: Card) => void;
}

export const CardsList = ({
  deckId,
  cards,
  onCardDeleted,
  onCardEdit,
}: CardsListProps) => {
  const [deletingCardId, setDeletingCardId] = useState<number>();
  const [deleteCardError, setDeleteCardError] = useState<string>();
  const [cardIdToDelete, setCardIdToDelete] = useState<number>();

  const handleDeleteCard = async (cardId: number) => {
    if (deletingCardId) {
      return;
    }

    setDeleteCardError(undefined);
    setDeletingCardId(cardId);

    try {
      const { error } = await deleteCard(deckId, cardId);

      if (error) {
        setDeleteCardError(error);
        return;
      }

      onCardDeleted(cardId);
    } finally {
      setDeletingCardId(undefined);
      setCardIdToDelete(undefined);
    }
  };

  const CardButtons = ({ card }: { card: Card }) => (
    <View
      style={{
        position: "absolute",
        top: 20,
        right: 20,
        display: "flex",
        flexDirection: "row",
        columnGap: 20,
      }}
    >
      <Pressable
        style={{
          padding: 1,
          width: 20,
          height: 20,
        }}
        onPress={() => onCardEdit(card)}
      >
        <EditIcon />
      </Pressable>
      <Pressable
        style={{
          width: 20,
          height: 20,
        }}
        onPress={() => setCardIdToDelete(card.c_id)}
      >
        <TrashIcon />
      </Pressable>
    </View>
  );

  return (
    <View
      style={{
        width: "100%",
        rowGap: 15,
      }}
    >
      {deleteCardError && <CText variant="inputError">{deleteCardError}</CText>}
      {cards.map((card) => (
        <View
          key={`card_${card.c_id}`}
          style={{
            padding: 20,
            borderRadius: 14,
            borderColor: COLORS.text.primary,
            borderWidth: 2,
            width: "100%",
          }}
        >
          <View
            style={{
              width: "100%",
              display: "flex",
              paddingBottom: 16,
              marginBottom: 16,
              borderBottomColor: COLORS.text.secondary,
              borderBottomWidth: 1,
            }}
          >
            <CText
              style={{
                color: COLORS.text.secondary,
                marginBottom: 4,
              }}
              bold
            >
              Front
            </CText>
            <CText>{card.word}</CText>
            {card.word_example && (
              <CText
                style={{
                  marginTop: 14,
                }}
              >
                {card.word_example}
              </CText>
            )}
          </View>
          <View
            style={{
              width: "100%",
              display: "flex",
            }}
          >
            <CText
              style={{
                color: COLORS.text.secondary,
                marginBottom: 4,
              }}
              bold
            >
              Back
            </CText>
            <CText>{card.translation}</CText>
            {card.word_example && (
              <CText
                style={{
                  marginTop: 14,
                }}
              >
                {card.trans_example}
              </CText>
            )}
          </View>
          {card.image && (
            <View
              style={{
                marginTop: 14,
                height: 120,
                width: "100%",
                overflow: "hidden",
              }}
            >
              <Image
                source={{ uri: getImageUrl(card.image) ?? card.image }}
                style={{ height: "100%", maxWidth: "auto",}}
                resizeMode="center"
              />
            </View>
          )}
          <CardButtons card={card} />
          {cardIdToDelete && (
            <Modal
              visible={!!cardIdToDelete}
              header="Are you sure?"
              submitLabel="Delete Card"
              subheader="This action will delete this card permanently"
              submitVariant="criticalPrimary"
              closeLabel="Cancel"
              onClose={() => setCardIdToDelete(undefined)}
              onSubmit={() =>
                cardIdToDelete && handleDeleteCard(cardIdToDelete)
              }
            />
          )}
        </View>
      ))}
    </View>
  );
};
