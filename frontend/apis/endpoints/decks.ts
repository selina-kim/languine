import {
  CreateDeckRequestPayload,
  Deck,
  GetSingleDeckResponseData,
} from "@/types/decks";
import client from "@/apis/client";

export const getDecks = (): Promise<{
  data: { decks: Deck[] };
  error: string | null;
}> => client.get(`/decks`);

export const getSingleDeck = (
  deckId: string | number,
): Promise<{
  data: GetSingleDeckResponseData;
  error: string | null;
}> => client.get(`/decks/${deckId}`);

export const createDeck = (data: CreateDeckRequestPayload) =>
  client.post(`/decks/new`, JSON.stringify(data));

export default { getDecks, getSingleDeck, createDeck };
