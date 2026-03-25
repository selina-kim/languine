import {
  Card,
  CardMutationResponseData,
  CreateCardRequestPayload,
  DeckCardsResponseData,
  ReviewCardsResponseData,
  UpdateCardRequestPayload,
} from "@/types/decks";
import client from "../client";

export const getCards = (
  deckId: string | number,
  page = 1,
  perPage = 50,
): Promise<{ data: DeckCardsResponseData; error: string | null }> =>
  client.get(`/decks/${deckId}/cards?page=${page}&per_page=${perPage}`);

export const getCard = (
  deckId: string | number,
  cardId: string | number,
): Promise<{ data: Card; error: string | null }> =>
  client.get(`/decks/${deckId}/cards/${cardId}`);

export const createCard = (
  deckId: string | number,
  data: CreateCardRequestPayload,
): Promise<{ data: CardMutationResponseData; error: string | null }> =>
  client.post(`/decks/${deckId}/card`, JSON.stringify(data));

export const updateCard = (
  deckId: string | number,
  cardId: string | number,
  data: UpdateCardRequestPayload,
): Promise<{ data: CardMutationResponseData; error: string | null }> =>
  client.post(`/decks/${deckId}/cards/${cardId}`, JSON.stringify(data));

export const deleteCard = (
  deckId: string | number,
  cardId: string | number,
): Promise<{ data: { message: string }; error: string | null }> =>
  client.delete(`/decks/${deckId}/cards/${cardId}`);

export const getReviewCards = (
  deckId: string | number,
  limit = 20,
): Promise<{ data: ReviewCardsResponseData; error: string | null }> =>
  client.get(`/decks/${deckId}/review?limit=${limit}`);

export default {
  getCards,
  getCard,
  createCard,
  updateCard,
  deleteCard,
  getReviewCards,
};
