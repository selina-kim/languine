export interface Deck {
  card_count: number;
  creation_date: string;
  d_id: string;
  deck_name: string;
  description?: string;
  is_public: boolean;
  last_reviewed: string | null;
  trans_lang: string;
  word_lang: string;
}

export interface DueDeck {
  d_id: string;
  deck_name: string;
  word_lang: string;
  trans_lang: string;
  last_reviewed: string | null;
  due_count: number;
  total_cards: number;
}

export interface Card {
  c_id: number;
  word: string;
  translation: string;
  word_example: string | null;
  trans_example: string | null;
  word_roman: string | null;
  trans_roman: string | null;
  image: string | null;
  word_audio?: string | null;
  trans_audio?: string | null;
  learning_state: number;
  difficulty: number;
  stability: number;
  due_date: string | null;
}

export interface DeckDetails {
  creation_date: string;
  d_id: number;
  deck_name: string;
  description?: string;
  is_public: boolean;
  last_reviewed: string | null;
  trans_lang: string;
  word_lang: string;
}

export interface GetSingleDeckResponseData {
  deck: DeckDetails;
  cards: Card[];
}

export interface CreateDeckRequestPayload {
  deck_name: string;
  word_lang: string;
  trans_lang: string;
  description?: string;
  is_public?: boolean;
  link?: string;
}

export interface UpdateDeckRequestPayload {
  deck_name?: string;
  description?: string;
  is_public?: boolean;
  link?: string;
}

export interface CreateCardRequestPayload {
  word: string;
  translation: string;
  word_example?: string;
  trans_example?: string;
  image?: string;
  word_audio?: string;
  trans_audio?: string;
  word_roman?: string;
  trans_roman?: string;
}

export interface UpdateCardRequestPayload {
  word?: string;
  translation?: string;
  word_example?: string;
  trans_example?: string;
  image?: string;
  word_audio?: string;
  trans_audio?: string;
  word_roman?: string;
  trans_roman?: string;
}

export interface CardListPagination {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface DeckCardsResponseData {
  cards: Card[];
  pagination: CardListPagination;
}

export interface CardMutationResponseData {
  message: string;
  card: Card;
}

export interface ReviewCardsResponseData {
  cards: Card[];
}
