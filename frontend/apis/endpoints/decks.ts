import {
  CreateDeckRequestPayload,
  Deck,
  DueDeck,
  GetSingleDeckResponseData,
  UpdateDeckRequestPayload,
} from "@/types/decks";
import client from "@/apis/client";
import { storage } from "@/utils/storage";

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

export const getRecentDecks = (
  limit = 3,
): Promise<{
  data: { decks: Deck[] };
  error: string | null;
}> => client.get(`/decks/recent?limit=${limit}`);

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

export const importDeck = (formData: FormData) =>
  client.post(`/decks/import`, formData);

export const exportDeck = async (
  deckId: string | number,
  format: "json" | "csv" | "anki" = "json",
): Promise<Response> => {
  const userData = await storage.getItem("user");
  if (!userData) {
    throw new Error("You must be logged in to export this deck.");
  }

  const parsedUser = JSON.parse(userData) as { token?: string };
  if (!parsedUser.token) {
    throw new Error("Missing authentication token.");
  }

  const baseUrl = process.env.EXPO_PUBLIC_API_URL;
  if (!baseUrl) {
    throw new Error("Missing API URL configuration.");
  }

  const exportUrl = `${baseUrl}/decks/${deckId}/export?format=${format}`;

  const response = await fetch(exportUrl, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${parsedUser.token}`,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Failed to export deck.");
  }

  return response;
};

export default {
  getDecks,
  getDecksWithDueCards,
  getRecentDecks,
  getSingleDeck,
  createDeck,
  updateDeck,
  deleteDeck,
  importDeck,
  exportDeck,
};
