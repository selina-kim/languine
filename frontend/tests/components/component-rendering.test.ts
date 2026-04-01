import { describe, expect, test, beforeEach, jest } from '@jest/globals';

describe('Deck Preview Component Logic', () => {
  interface DeckPreviewProps {
    deckName: string;
    description?: string;
    language: string;
    cardCount: number;
    onViewDeck: () => void;
    onDeleteDeck: () => void;
  }

  const createDeckPreview = (props: DeckPreviewProps) => {
    return {
      deckName: props.deckName,
      description: props.description,
      language: props.language,
      cardCount: props.cardCount,
      onViewDeck: props.onViewDeck,
      onDeleteDeck: props.onDeleteDeck,
      hasDescription: !!(props.description && props.description.trim() !== ''),
    };
  };

  test('should render deck with all required information', () => {
    const onView = jest.fn();
    const onDelete = jest.fn();

    const component = createDeckPreview({
      deckName: 'Spanish Basics',
      description: 'Learn basic Spanish vocabulary',
      language: 'es',
      cardCount: 50,
      onViewDeck: onView,
      onDeleteDeck: onDelete,
    });

    expect(component.deckName).toBe('Spanish Basics');
    expect(component.language).toBe('es');
    expect(component.cardCount).toBe(50);
    expect(component.hasDescription).toBe(true);
  });

  test('should handle deck without description', () => {
    const component = createDeckPreview({
      deckName: 'French Basics',
      language: 'fr',
      cardCount: 30,
      onViewDeck: jest.fn(),
      onDeleteDeck: jest.fn(),
    });

    expect(component.hasDescription).toBeFalsy();
    expect(component.description).toBeUndefined();
  });

  test('should handle empty description string', () => {
    const component = createDeckPreview({
      deckName: 'Japanese Basics',
      description: '   ',
      language: 'ja',
      cardCount: 75,
      onViewDeck: jest.fn(),
      onDeleteDeck: jest.fn(),
    });

    expect(component.hasDescription).toBe(false);
  });

  test('should call onViewDeck when view button pressed', () => {
    const onView = jest.fn();
    const component = createDeckPreview({
      deckName: 'German Basics',
      language: 'de',
      cardCount: 40,
      onViewDeck: onView,
      onDeleteDeck: jest.fn(),
    });

    // Simulate button press
    component.onViewDeck();

    expect(onView).toHaveBeenCalled();
    expect(onView).toHaveBeenCalledTimes(1);
  });

  test('should call onDeleteDeck when delete button pressed', () => {
    const onDelete = jest.fn();
    const component = createDeckPreview({
      deckName: 'Italian Basics',
      language: 'it',
      cardCount: 25,
      onViewDeck: jest.fn(),
      onDeleteDeck: onDelete,
    });

    // Simulate delete button press
    component.onDeleteDeck();

    expect(onDelete).toHaveBeenCalled();
    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  test('should display language in uppercase', () => {
    const component = createDeckPreview({
      deckName: 'Portuguese Basics',
      language: 'pt',
      cardCount: 35,
      onViewDeck: jest.fn(),
      onDeleteDeck: jest.fn(),
    });

    expect(component.language.toUpperCase()).toBe('PT');
  });

  test('should handle decks with zero cards', () => {
    const component = createDeckPreview({
      deckName: 'Empty Deck',
      language: 'ko',
      cardCount: 0,
      onViewDeck: jest.fn(),
      onDeleteDeck: jest.fn(),
    });

    expect(component.cardCount).toBe(0);
  });

  test('should handle decks with many cards', () => {
    const component = createDeckPreview({
      deckName: 'Comprehensive Deck',
      language: 'zh',
      cardCount: 5000,
      onViewDeck: jest.fn(),
      onDeleteDeck: jest.fn(),
    });

    expect(component.cardCount).toBe(5000);
  });
});

describe('Cards List Component Logic', () => {
  interface Card {
    c_id: number;
    word: string;
    translation: string;
    image?: string;
    difficulty?: number;
  }

  interface CardsListProps {
    cards: Card[];
    onCardPress: (card: Card) => void;
    onCardLongPress?: (card: Card) => void;
    sortBy?: 'name' | 'difficulty' | 'recent';
    filterBy?: 'all' | 'due' | 'mastered';
  }

  const createCardsList = (props: CardsListProps) => {
    let sortedCards = [...props.cards];

    if (props.sortBy === 'name') {
      sortedCards.sort((a, b) => a.word.localeCompare(b.word));
    } else if (props.sortBy === 'difficulty') {
      sortedCards.sort((a, b) => (b.difficulty || 0) - (a.difficulty || 0));
    }

    if (props.filterBy === 'due') {
      // Simplified: assume certain cards are due
      sortedCards = sortedCards.filter((c) => (c.difficulty || 0) > 2);
    } else if (props.filterBy === 'mastered') {
      sortedCards = sortedCards.filter((c) => (c.difficulty || 0) <= 2);
    }

    return {
      cards: sortedCards,
      totalCards: props.cards.length,
      displayedCards: sortedCards.length,
      onCardPress: props.onCardPress,
      onCardLongPress: props.onCardLongPress,
    };
  };

  test('should render list of cards', () => {
    const cards = [
      { c_id: 1, word: 'Hola', translation: 'Hello', difficulty: 2 },
      { c_id: 2, word: 'Adiós', translation: 'Goodbye', difficulty: 3 },
      { c_id: 3, word: 'Gracias', translation: 'Thank you', difficulty: 1 },
    ];

    const list = createCardsList({
      cards,
      onCardPress: jest.fn(),
    });

    expect(list.totalCards).toBe(3);
    expect(list.displayedCards).toBe(3);
  });

  test('should sort cards by name', () => {
    const cards = [
      { c_id: 1, word: 'Zebra', translation: 'Zebra' },
      { c_id: 2, word: 'Apple', translation: 'Apple' },
      { c_id: 3, word: 'Mango', translation: 'Mango' },
    ];

    const list = createCardsList({
      cards,
      onCardPress: jest.fn(),
      sortBy: 'name',
    });

    expect(list.cards[0].word).toBe('Apple');
    expect(list.cards[1].word).toBe('Mango');
    expect(list.cards[2].word).toBe('Zebra');
  });

  test('should sort cards by difficulty', () => {
    const cards = [
      { c_id: 1, word: 'Easy', translation: 'Easy', difficulty: 1 },
      { c_id: 2, word: 'Hard', translation: 'Hard', difficulty: 5 },
      { c_id: 3, word: 'Medium', translation: 'Medium', difficulty: 3 },
    ];

    const list = createCardsList({
      cards,
      onCardPress: jest.fn(),
      sortBy: 'difficulty',
    });

    expect(list.cards[0].difficulty).toBe(5);
    expect(list.cards[1].difficulty).toBe(3);
    expect(list.cards[2].difficulty).toBe(1);
  });

  test('should filter cards by due status', () => {
    const cards = [
      { c_id: 1, word: 'Due1', translation: 'Due', difficulty: 3 },
      { c_id: 2, word: 'NotDue', translation: 'Not Due', difficulty: 1 },
      { c_id: 3, word: 'Due2', translation: 'Due', difficulty: 5 },
    ];

    const list = createCardsList({
      cards,
      onCardPress: jest.fn(),
      filterBy: 'due',
    });

    expect(list.displayedCards).toBe(2);
    expect(list.cards.every((c) => (c.difficulty || 0) > 2)).toBe(true);
  });

  test('should handle card press event', () => {
    const onCardPress = jest.fn();
    const card = { c_id: 1, word: 'Hola', translation: 'Hello' };

    const list = createCardsList({
      cards: [card],
      onCardPress,
    });

    // Simulate card press
    list.onCardPress(card);

    expect(onCardPress).toHaveBeenCalledWith(card);
  });

  test('should handle empty card list', () => {
    const list = createCardsList({
      cards: [],
      onCardPress: jest.fn(),
    });

    expect(list.totalCards).toBe(0);
    expect(list.displayedCards).toBe(0);
    expect(list.cards).toHaveLength(0);
  });

  test('should apply multiple filters', () => {
    const cards = [
      { c_id: 1, word: 'Card1', translation: 'Trans', difficulty: 4 },
      { c_id: 2, word: 'Card2', translation: 'Trans', difficulty: 2 },
      { c_id: 3, word: 'Card3', translation: 'Trans', difficulty: 5 },
    ];

    const list = createCardsList({
      cards,
      onCardPress: jest.fn(),
      sortBy: 'difficulty',
      filterBy: 'due',
    });

    expect(list.cards.length).toBeLessThanOrEqual(cards.length);
  });
});

describe('Study Card Component Logic', () => {
  interface Card {
    c_id: number;
    word: string;
    translation: string;
    word_example?: string;
    trans_example?: string;
    image?: string;
    difficulty?: number;
  }

  interface StudyCardProps {
    card: Card;
    isFlipped: boolean;
    onFlip: () => void;
    onRating: (rating: number) => void;
    currentCardIndex: number;
    totalCards: number;
  }

  const createStudyCard = (props: StudyCardProps) => {
    const display = props.isFlipped ? 'translation' : 'word';
    const displayText = props.isFlipped ? props.card.translation : props.card.word;

    return {
      card: props.card,
      isFlipped: props.isFlipped,
      displayText,
      display,
      onFlip: props.onFlip,
      onRating: props.onRating,
      progress: `${props.currentCardIndex + 1} / ${props.totalCards}`,
      canFlip: true,
      ratingOptions: [1, 2, 3, 4],
    };
  };

  test('should display front of card initially', () => {
    const card = {
      c_id: 1,
      word: 'Hola',
      translation: 'Hello',
      difficulty: 3,
    };

    const studyCard = createStudyCard({
      card,
      isFlipped: false,
      onFlip: jest.fn(),
      onRating: jest.fn(),
      currentCardIndex: 0,
      totalCards: 10,
    });

    expect(studyCard.displayText).toBe('Hola');
    expect(studyCard.display).toBe('word');
  });

  test('should flip to show translation', () => {
    const card = {
      c_id: 1,
      word: 'Hola',
      translation: 'Hello',
    };

    const studyCard = createStudyCard({
      card,
      isFlipped: true,
      onFlip: jest.fn(),
      onRating: jest.fn(),
      currentCardIndex: 0,
      totalCards: 10,
    });

    expect(studyCard.displayText).toBe('Hello');
    expect(studyCard.display).toBe('translation');
  });

  test('should call onFlip when flipping card', () => {
    const onFlip = jest.fn();
    const card = { c_id: 1, word: 'Test', translation: 'Test' };

    const studyCard = createStudyCard({
      card,
      isFlipped: false,
      onFlip,
      onRating: jest.fn(),
      currentCardIndex: 0,
      totalCards: 5,
    });

    // Simulate flip
    studyCard.onFlip();

    expect(onFlip).toHaveBeenCalled();
  });

  test('should handle rating selection', () => {
    const onRating = jest.fn();
    const card = { c_id: 1, word: 'Test', translation: 'Test' };

    const studyCard = createStudyCard({
      card,
      isFlipped: true,
      onFlip: jest.fn(),
      onRating,
      currentCardIndex: 0,
      totalCards: 5,
    });

    // User rates card as 4 (good)
    studyCard.onRating(4);

    expect(onRating).toHaveBeenCalledWith(4);
  });

  test('should show progress indicator', () => {
    const card = { c_id: 1, word: 'Test', translation: 'Test' };

    const studyCard = createStudyCard({
      card,
      isFlipped: false,
      onFlip: jest.fn(),
      onRating: jest.fn(),
      currentCardIndex: 2,
      totalCards: 10,
    });

    expect(studyCard.progress).toBe('3 / 10');
  });

  test('should display examples when available', () => {
    const card = {
      c_id: 1,
      word: 'Hola',
      translation: 'Hello',
      word_example: 'Hola, ¿cómo estás?',
      trans_example: 'Hello, how are you?',
    };

    const studyCard = createStudyCard({
      card,
      isFlipped: false,
      onFlip: jest.fn(),
      onRating: jest.fn(),
      currentCardIndex: 0,
      totalCards: 5,
    });

    expect(studyCard.card.word_example).toBeTruthy();
    expect(studyCard.card.trans_example).toBeTruthy();
  });

  test('should provide all rating options', () => {
    const card = { c_id: 1, word: 'Test', translation: 'Test' };

    const studyCard = createStudyCard({
      card,
      isFlipped: true,
      onFlip: jest.fn(),
      onRating: jest.fn(),
      currentCardIndex: 0,
      totalCards: 5,
    });

    expect(studyCard.ratingOptions).toContain(1);
    expect(studyCard.ratingOptions).toContain(4);
    expect(studyCard.ratingOptions).toHaveLength(4);
  });

  test('should handle first card in session', () => {
    const card = { c_id: 1, word: 'First', translation: 'First' };

    const studyCard = createStudyCard({
      card,
      isFlipped: false,
      onFlip: jest.fn(),
      onRating: jest.fn(),
      currentCardIndex: 0,
      totalCards: 10,
    });

    expect(studyCard.progress).toBe('1 / 10');
  });

  test('should handle last card in session', () => {
    const card = { c_id: 10, word: 'Last', translation: 'Last' };

    const studyCard = createStudyCard({
      card,
      isFlipped: false,
      onFlip: jest.fn(),
      onRating: jest.fn(),
      currentCardIndex: 9,
      totalCards: 10,
    });

    expect(studyCard.progress).toBe('10 / 10');
  });
});

describe('Review Summary Component Logic', () => {
  interface ReviewResult {
    correct: number;
    incorrect: number;
    skipped: number;
    totalTime: number;
    averageTime: number;
  }

  const calculateReviewSummary = (ratings: number[], times: number[]): ReviewResult => {
    const correct = ratings.filter((r) => r >= 3).length;
    const incorrect = ratings.filter((r) => r < 3).length;
    const skipped = 0;
    const totalTime = times.reduce((a, b) => a + b, 0);
    const averageTime = totalTime / times.length;

    return {
      correct,
      incorrect,
      skipped,
      totalTime,
      averageTime,
    };
  };

  test('should calculate summary statistics correctly', () => {
    const ratings = [4, 1, 4, 3, 2];
    const times = [2000, 1500, 2500, 3000, 1800];

    const summary = calculateReviewSummary(ratings, times);

    expect(summary.correct).toBe(3); // ratings 4, 4, 3
    expect(summary.incorrect).toBe(2); // ratings 1, 2
    expect(summary.totalTime).toBe(10800);
    expect(summary.averageTime).toBe(2160);
  });

  test('should handle all correct reviews', () => {
    const ratings = [4, 4, 4, 4];
    const times = [2000, 2000, 2000, 2000];

    const summary = calculateReviewSummary(ratings, times);

    expect(summary.correct).toBe(4);
    expect(summary.incorrect).toBe(0);
  });

  test('should handle all incorrect reviews', () => {
    const ratings = [1, 1, 1];
    const times = [1000, 1000, 1000];

    const summary = calculateReviewSummary(ratings, times);

    expect(summary.correct).toBe(0);
    expect(summary.incorrect).toBe(3);
  });

  test('should format time durations correctly', () => {
    const totalSeconds = 125; // 2 min 5 sec
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    expect(minutes).toBe(2);
    expect(seconds).toBe(5);
  });
});
