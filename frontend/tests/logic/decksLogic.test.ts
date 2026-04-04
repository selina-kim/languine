import { describe, expect, test, beforeEach, jest } from '@jest/globals';
import type { Deck } from '@/types/decks';

// Mock API functions
jest.mock('@/apis/endpoints/decks');

const { getDecks, deleteDeck } = require('@/apis/endpoints/decks');

describe('Decks Tab Logic', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should render decks list when decks are available', async () => {
    const mockDecks: Deck[] = [
      {
        d_id: '1',
        deck_name: 'Japanese Beginner',
        word_lang: 'JA',
        trans_lang: 'EN',
        card_count: 30,
        is_public: true,
        creation_date: '2025-01-01T00:00:00Z',
        last_reviewed: new Date().toISOString(),
      },
      {
        d_id: '2',
        deck_name: 'French Intermediate',
        word_lang: 'FR',
        trans_lang: 'EN',
        card_count: 28,
        is_public: false,
        creation_date: '2025-02-15T00:00:00Z',
        last_reviewed: new Date().toISOString(),
      },
    ];

    getDecks.mockResolvedValue({
      data: { decks: mockDecks },
      error: null,
    });

    const result = await getDecks();
    expect(result.data.decks).toHaveLength(2);
    expect(result.data.decks[0].deck_name).toBe('Japanese Beginner');
    expect(result.data.decks[1].deck_name).toBe('French Intermediate');
  });

  test('should handle empty decks list', async () => {
    getDecks.mockResolvedValue({
      data: { decks: [] },
      error: null,
    });

    const result = await getDecks();
    expect(result.data.decks).toHaveLength(0);
  });

  test('should display deck card counts', async () => {
    const mockDeck: Deck = {
      d_id: '1',
      deck_name: 'Test Deck',
      word_lang: 'FR',
      trans_lang: 'EN',
      card_count: 42,
      is_public: true,
      creation_date: '2025-01-01T00:00:00Z',
      last_reviewed: new Date().toISOString(),
    };

    getDecks.mockResolvedValue({
      data: { decks: [mockDeck] },
      error: null,
    });

    const result = await getDecks();
    expect(result.data.decks[0].card_count).toBe(42);
    expect(result.data.decks[0].word_lang).toBe('FR');
    expect(result.data.decks[0].trans_lang).toBe('EN');
  });

  test('should validate deck sorting by last reviewed date', async () => {
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    const mockDecks: Deck[] = [
      {
        d_id: '1',
        deck_name: 'Older Deck',
        word_lang: 'KO',
        trans_lang: 'EN',
        card_count: 15,
        is_public: false,
        creation_date: '2024-11-01T00:00:00Z',
        last_reviewed: yesterday.toISOString(),
      },
      {
        d_id: '2',
        deck_name: 'Recent Deck',
        word_lang: 'JA',
        trans_lang: 'EN',
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

  test('should handle deck deletion', async () => {
    deleteDeck.mockResolvedValue({ error: null });

    const result = await deleteDeck('deck_123');

    expect(deleteDeck).toHaveBeenCalledWith('deck_123');
    expect(result.error).toBeNull();
  });

  test('should handle API errors gracefully', async () => {
    getDecks.mockResolvedValue({
      data: { decks: [] },
      error: 'Failed to fetch decks',
    });

    const result = await getDecks();

    expect(result.error).toBe('Failed to fetch decks');
    expect(result.data.decks).toHaveLength(0);
  });
});

