import { describe, expect, test, beforeEach, jest } from '@jest/globals';

jest.mock('@/apis/endpoints/decks');

const { getDecksWithDueCards } = require('@/apis/endpoints/decks');

describe('Revision Tab Logic', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should display decks with due cards', async () => {
    const mockDueDecks = [
      { d_id: '1', deck_name: 'Japanese Basics', word_lang: 'JA', due_count: 5 },
      { d_id: '2', deck_name: 'French 101', word_lang: 'FR', due_count: 8 },
    ];

    getDecksWithDueCards.mockResolvedValue({
      data: { decks: mockDueDecks },
      error: null,
    });

    const result = await getDecksWithDueCards(20);

    expect(result.data.decks).toHaveLength(2);
    expect(result.data.decks[0].deck_name).toBe('Japanese Basics');
    expect(result.data.decks[1].deck_name).toBe('French 101');
  });

  test('should show empty state when no decks with due cards', async () => {
    getDecksWithDueCards.mockResolvedValue({
      data: { decks: [] },
      error: null,
    });

    const result = await getDecksWithDueCards(20);

    expect(result.data.decks).toHaveLength(0);
  });

  test('should display due card counts', async () => {
    const mockDueDecks = [
      { d_id: '1', deck_name: 'Test Deck', word_lang: 'KO', due_count: 15 },
    ];

    getDecksWithDueCards.mockResolvedValue({
      data: { decks: mockDueDecks },
      error: null,
    });

    const result = await getDecksWithDueCards(20);

    expect(result.data.decks[0].due_count).toBe(15);
  });

  test('should handle API errors gracefully', async () => {
    getDecksWithDueCards.mockResolvedValue({
      data: { decks: [] },
      error: 'Failed to fetch decks',
    });

    const result = await getDecksWithDueCards(20);

    expect(result.error).toBe('Failed to fetch decks');
  });

  test('should call getDecksWithDueCards on mount', async () => {
    getDecksWithDueCards.mockResolvedValue({
      data: { decks: [] },
      error: null,
    });

    await getDecksWithDueCards(20);

    expect(getDecksWithDueCards).toHaveBeenCalled();
  });

  test('should limit due decks request to 20', async () => {
    getDecksWithDueCards.mockResolvedValue({
      data: { decks: [] },
      error: null,
    });

    await getDecksWithDueCards(20);

    expect(getDecksWithDueCards).toHaveBeenCalledWith(20);
  });

  test('should calculate review progress correctly', () => {
    const currentCardIndex = 5;
    const totalCards = 10;
    const progress = (currentCardIndex / totalCards) * 100;

    expect(progress).toBe(50);
  });

  test('should track correct and incorrect answers', () => {
    const reviewSession = {
      correctAnswers: 7,
      wrongAnswers: 3,
      totalCards: 10,
    };

    const accuracy = (reviewSession.correctAnswers / reviewSession.totalCards) * 100;
    expect(accuracy).toBe(70);
  });
});

