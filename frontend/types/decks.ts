export interface Deck {
  deck_id: string;
  deck_name: string;
  word_lang: string;
  trans_lang: string;
  description?: string;
  is_public: boolean;
  link?: string;
  created_at: string;
}

export interface CreateDeckRequestPayload {
  deck_name: string;
  word_lang: string;
  trans_lang: string;
  description?: string;
  is_public?: boolean;
  link?: string;
}
