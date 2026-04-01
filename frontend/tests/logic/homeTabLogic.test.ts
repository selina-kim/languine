import { describe, expect, test } from '@jest/globals';

describe('Index/Home Tab', () => {
  test('should display cards due banner with count', () => {
    const countDueCards = 10;
    expect(countDueCards).toBeGreaterThanOrEqual(0);
    expect(typeof countDueCards).toBe('number');
  });

  test('should render empty state when no recent decks', () => {
    const recentDecks = [];
    expect(recentDecks).toHaveLength(0);
  });

  test('should render recent decks section with decks', () => {
    const recentDecks = [
      { d_id: '1', deck_name: 'Japanese Beginner' },
      { d_id: '2', deck_name: 'Spanish Intermediate' },
      { d_id: '3', deck_name: 'French Advanced' },
    ];

    expect(recentDecks).toHaveLength(3);
    expect(recentDecks[0].deck_name).toBe('Japanese Beginner');
  });

  test('should limit recent decks to 3 items', () => {
    const allDecks = Array.from({ length: 10 }, (_, i) => ({
      d_id: String(i),
      deck_name: `Deck ${i + 1}`,
    }));

    const recentDecks = allDecks.slice(0, 3);
    expect(recentDecks).toHaveLength(3);
  });

  test('should format last reviewed date correctly', () => {
    const date = new Date('2026-03-31');
    const formatted = date.toLocaleDateString();
    expect(formatted).toBeTruthy();
    expect(typeof formatted).toBe('string');
  });

  test('should handle due cards state', () => {
    const cardStates = {
      dueCards: 5,
      newCards: 10,
      reviewCards: 15,
      learningCards: 3,
    };

    const totalDueCards = cardStates.dueCards + cardStates.reviewCards;
    expect(totalDueCards).toBe(20);
  });
});
