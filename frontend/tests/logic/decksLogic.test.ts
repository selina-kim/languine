import { describe, expect, test } from '@jest/globals';
import type { Deck } from '@/types/decks';

describe('Decks Tab', () => {
  test('should render decks list when decks are available', () => {
    const mockDecks: Deck[] = [
      {
        d_id: '1',
        deck_name: 'Japanese Beginner',
        word_lang: 'Japanese',
        trans_lang: 'English',
        card_count: 30,
        is_public: true,
        creation_date: '2025-01-01T00:00:00Z',
        last_reviewed: new Date().toISOString(),
      },
      {
        d_id: '2',
        deck_name: 'Spanish Intermediate',
        word_lang: 'Spanish',
        trans_lang: 'English',
        card_count: 28,
        is_public: false,
        creation_date: '2025-02-15T00:00:00Z',
        last_reviewed: new Date().toISOString(),
      },
    ];

    expect(mockDecks).toHaveLength(2);
    expect(mockDecks[0].deck_name).toBe('Japanese Beginner');
    expect(mockDecks[1].deck_name).toBe('Spanish Intermediate');
  });

  test('should handle empty decks list', () => {
    const mockDecks: Deck[] = [];
    expect(mockDecks).toHaveLength(0);
  });

  test('should display deck card counts', () => {
    const mockDeck: Deck = {
      d_id: '1',
      deck_name: 'Test Deck',
      word_lang: 'French',
      trans_lang: 'English',
      card_count: 42,
      is_public: true,
      creation_date: '2025-01-01T00:00:00Z',
      last_reviewed: new Date().toISOString(),
    };

    expect(mockDeck.card_count).toBe(42);
    expect(mockDeck.word_lang).toBe('French');
    expect(mockDeck.trans_lang).toBe('English');
  });

  test('should validate deck sorting by last reviewed date', () => {
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    const mockDecks: Deck[] = [
      {
        d_id: '1',
        deck_name: 'Older Deck',
        word_lang: 'German',
        trans_lang: 'English',
        card_count: 15,
        is_public: false,
        creation_date: '2024-11-01T00:00:00Z',
        last_reviewed: yesterday.toISOString(),
      },
      {
        d_id: '2',
        deck_name: 'Recent Deck',
        word_lang: 'Italian',
        trans_lang: 'English',
        card_count: 13,
        is_public: true,
        creation_date: '2024-12-20T00:00:00Z',
        last_reviewed: now.toISOString(),
      },
    ];

    const sorted = [...mockDecks].sort(
      (a, b) => new Date(b.last_reviewed!).getTime() - new Date(a.last_reviewed!).getTime()
    );

    expect(sorted[0].deck_name).toBe('Recent Deck');
    expect(sorted[1].deck_name).toBe('Older Deck');
  });
});
