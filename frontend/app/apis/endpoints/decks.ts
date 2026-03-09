import { CreateDeckRequestPayload } from "@/types/decks";
import client from "../client";

// TODO
export const getDecks = () => client.get("");

// TODO
export const createDeck = (data: CreateDeckRequestPayload) =>
  client.post(`/decks/new`, JSON.stringify(data));

export default { getDecks, createDeck };
