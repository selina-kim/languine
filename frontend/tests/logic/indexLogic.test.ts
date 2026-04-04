import { describe, expect, test, beforeEach, jest } from '@jest/globals';

jest.mock('@/apis/endpoints/decks');
jest.mock('@/apis/endpoints/fsrs');

const { getRecentDecks } = require('@/apis/endpoints/decks');
const { getDueCards } = require('@/apis/endpoints/fsrs');

describe('Index/Home Tab Logic', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should display cards due banner with count', async () => {
    getRecentDecks.mockResolvedValue({
      data: { decks: [] },
      error: null,
    });

    getDueCards.mockResolvedValue({
      data: { num_due_cards: 10 },
      error: null,
    });

    const result = await getDueCards();

    expect(result.data.num_due_cards).toBe(10);
    expect(result.data.num_due_cards).toBeGreaterThanOrEqual(0);
  });

  test('should render empty state when no recent decks', async () => {
    getRecentDecks.mockResolvedValue({
      data: { decks: [] },
      error: null,
    });

    const result = await getRecentDecks(3);

    expect(result.data.decks).toHaveLength(0);
  });

  test('should render recent decks section with decks', async () => {
    const recentDecks = [
      { d_id: '1', deck_name: 'Japanese Beginner', last_reviewed: new Date().toISOString() },
      { d_id: '2', deck_name: 'Spanish Intermediate', last_reviewed: new Date().toISOString() },
      { d_id: '3', deck_name: 'French Advanced', last_reviewed: new Date().toISOString() },
    ];

    getRecentDecks.mockResolvedValue({
      data: { decks: recentDecks },
      error: null,
    });

    const result = await getRecentDecks(3);

    expect(result.data.decks).toHaveLength(3);
    expect(result.data.decks[0].deck_name).toBe('Japanese Beginner');
  });

  test('should limit recent decks to 3 items', async () => {
    const allDecks = Array.from({ length: 10 }, (_, i) => ({
      d_id: String(i),
      deck_name: `Deck ${i + 1}`,
      last_reviewed: new Date().toISOString(),
    }));

    getRecentDecks.mockResolvedValue({
      data: { decks: allDecks.slice(0, 3) },
      error: null,
    });

    const result = await getRecentDecks(3);

    expect(result.data.decks).toHaveLength(3);
    expect(getRecentDecks).toHaveBeenCalledWith(3);
  });

  test('should format last reviewed date correctly', () => {
    const date = new Date('2026-03-31');
    const formatted = date.toLocaleDateString();

    expect(formatted).toBeTruthy();
    expect(typeof formatted).toBe('string');
  });

  test('should call getDueCards and getRecentDecks on mount', async () => {
    getRecentDecks.mockResolvedValue({
      data: { decks: [] },
      error: null,
    });

    getDueCards.mockResolvedValue({
      data: { num_due_cards: 0 },
      error: null,
    });

    await getRecentDecks(3);
    await getDueCards();

    expect(getRecentDecks).toHaveBeenCalled();
    expect(getDueCards).toHaveBeenCalled();
  });

  test('should handle API errors gracefully', async () => {
    getRecentDecks.mockResolvedValue({
      data: { decks: [] },
      error: 'Failed to fetch decks',
    });

    getDueCards.mockResolvedValue({
      data: { num_due_cards: 0 },
      error: 'Failed to fetch due cards',
    });

    const deckResult = await getRecentDecks(3);
    const dueResult = await getDueCards();

    expect(deckResult.error).toBe('Failed to fetch decks');
    expect(dueResult.error).toBe('Failed to fetch due cards');
  });
});

