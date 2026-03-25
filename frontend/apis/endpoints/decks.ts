import {
  CreateDeckRequestPayload,
  Deck,
  DueDeck,
  GetSingleDeckResponseData,
  UpdateDeckRequestPayload,
} from "@/types/decks";
import client from "@/apis/client";

export const getDecks = (): Promise<{
  data: { decks: Deck[] };
  error: string | null;
}> => client.get(`/decks`);

export const getDecksWithDueCards = (
  limit = 20,
): Promise<{
  data: { decks: DueDeck[] };
  error: string | null;
}> => client.get(`/decks/due?limit=${limit}`);

export const getSingleDeck = (
  deckId: string | number,
): Promise<{
  data: GetSingleDeckResponseData;
  error: string | null;
}> => client.get(`/decks/${deckId}`);

export const createDeck = (data: CreateDeckRequestPayload) =>
  client.post(`/decks/new`, JSON.stringify(data));

export const updateDeck = (
  deckId: string | number,
  data: UpdateDeckRequestPayload,
) => client.put(`/decks/${deckId}`, JSON.stringify(data));

export const deleteDeck = (deckId: string | number) =>
  client.delete(`/decks/${deckId}`);

export default {
  getDecks,
  getDecksWithDueCards,
  getSingleDeck,
  createDeck,
  updateDeck,
  deleteDeck,
};
