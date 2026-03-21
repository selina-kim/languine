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

export interface Card {
  c_id: number;
  word: string;
  translation: string;
  definition: string | null;
  word_example: string | null;
  trans_example: string | null;
  word_roman: string | null;
  trans_roman: string | null;
  image: string | null;
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
