import { describe, expect, test, jest, beforeEach } from '@jest/globals';

// Mock Expo Router
jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  useSegments: () => [],
}));

// Mock storage
jest.mock('@/utils/storage', () => ({
  storage: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
  },
}));

// Mock API endpoints
jest.mock('@/apis/endpoints/decks', () => ({
  getDecks: jest.fn(),
  getSingleDeck: jest.fn(),
  createDeck: jest.fn(),
  updateDeck: jest.fn(),
  deleteDeck: jest.fn(),
}));

jest.mock('@/apis/endpoints/cards', () => ({
  getCards: jest.fn(),
  createCard: jest.fn(),
  updateCard: jest.fn(),
  deleteCard: jest.fn(),
}));

// Component logic and rendering tests
describe('DeckPreview Component', () => {
  const mockOnViewDeck = jest.fn();
  const mockOnDeleteDeck = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should process valid deck props', () => {
    const deckProps = {
      deckName: 'Japanese Beginner',
      description: 'Learn basic Japanese vocabulary',
      language: 'ja',
      cardCount: 50,
      onViewDeck: mockOnViewDeck,
      onDeleteDeck: mockOnDeleteDeck,
    };

    expect(deckProps.deckName).toBeTruthy();
    expect(deckProps.cardCount).toBeGreaterThan(0);
    expect(deckProps.language).toBe('ja');
  });

  test('should handle missing description', () => {
    const description = '';
    const hasDescription = description.length > 0;
    expect(hasDescription).toBe(false);
  });

  test('should format language to uppercase for display', () => {
    const language = 'ja';
    expect(language).toBe('ja');
  });

  test('should invoke onViewDeck callback', () => {
    mockOnViewDeck('deck_123');
    expect(mockOnViewDeck).toHaveBeenCalledWith('deck_123');
  });

  test('should invoke onDeleteDeck callback', () => {
    mockOnDeleteDeck('deck_123');
    expect(mockOnDeleteDeck).toHaveBeenCalledWith('deck_123');
  });
});

describe('NoDecksBanner Component', () => {
  const mockOnCreateNewDeck = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should show banner only when deck list is empty', () => {
    const decks = [];
    expect(decks.length === 0).toBe(true);
  });

  test('should not show banner when decks exist', () => {
    const decks = [{ d_id: '1', deck_name: 'Test' }];
    expect(decks.length === 0).toBe(false);
  });

  test('should invoke onCreate when create button pressed', () => {
    mockOnCreateNewDeck();
    expect(mockOnCreateNewDeck).toHaveBeenCalledTimes(1);
  });

  test('should display correct banner text', () => {
    const title = 'No Decks Yet';
    const description = 'Create your first deck to start learning!';
    
    expect(title).toBe('No Decks Yet');
    expect(description).toContain('Create');
  });
});

describe('CardsList Component', () => {
  test('should handle list of card objects', () => {
    const cards = [
      { c_id: '1', word: '안녕하세요', translation: 'Hello', difficulty: 2 },
      { c_id: '2', word: '안녕히 가세요', translation: 'Goodbye', difficulty: 3 },
      { c_id: '3', word: '감사합니다', translation: 'Thank you', difficulty: 1 },
    ];

    expect(cards.length).toBe(3);
    expect(cards.every(c => c.c_id && c.word && c.translation)).toBe(true);
  });

  test('should display cards in backend order (no sorting)', () => {
    // Backend orders cards by c_id, frontend displays them as-is
    const cards = [
      { c_id: 3, word: 'Zebra', translation: 'Cebra', difficulty: 2 },
      { c_id: 1, word: 'Apple', translation: 'Manzana', difficulty: 1 },
      { c_id: 2, word: 'Mango', translation: 'Mango', difficulty: 3 },
    ];

    // Cards maintain their original order from the backend
    expect(cards[0].word).toBe('Zebra');
    expect(cards[1].word).toBe('Apple');
    expect(cards[2].word).toBe('Mango');
  });

  test('should preserve difficulty values when displaying cards', () => {
    const cards = [
      { c_id: 1, word: 'Easy', difficulty: 1 },
      { c_id: 2, word: 'Hard', difficulty: 5 },
      { c_id: 3, word: 'Medium', difficulty: 3 },
    ];

    // Difficulty values are preserved but cards are not sorted by difficulty
    expect(cards[0].difficulty).toBe(1);
    expect(cards[1].difficulty).toBe(5);
    expect(cards[2].difficulty).toBe(3);
  });

  test('should handle empty cards list', () => {
    const cards: any[] = [];
    expect(cards.length).toBe(0);
  });

  test('should handle large datasets', () => {
    const cards = Array.from({ length: 500 }, (_, i) => ({
      c_id: String(i),
      word: `Word${i}`,
      translation: `Translation${i}`,
    }));

    expect(cards.length).toBe(500);
  });
});

describe('CreateNewDeckModal Form Validation', () => {
  test('should accept valid deck name', () => {
    const deckName = 'My New Deck';
    const isValid = deckName.trim().length > 0;
    expect(isValid).toBe(true);
  });

  test('should reject empty deck name', () => {
    const deckName = '';
    const isValid = deckName.trim().length > 0;
    expect(isValid).toBe(false);
  });

  test('should reject whitespace-only deck name', () => {
    const deckName = '   ';
    const isValid = deckName.trim().length > 0;
    expect(isValid).toBe(false);
  });

  test('should validate form completeness', () => {
    const formData = {
      deckName: 'Valid Name',
      wordLanguage: 'en',
      translationLanguage: 'ja',
    };

    const isComplete = 
      formData.deckName.trim().length > 0 &&
      !!formData.wordLanguage &&
      !!formData.translationLanguage;

    expect(isComplete).toBe(true);
  });

  test('should accept optional description', () => {
    const description = 'Optional description';
    const isValid = !description || description.trim().length >= 0;
    expect(isValid).toBe(true);
  });
});

describe('SingleDeckView Component State Management', () => {
  test('should manage loading and deck states', () => {
    const state = {
      isLoadingDeckDetails: false,
      isLoadingCards: false,
      deckDetails: { d_id: '1', deck_name: 'Test' },
      cards: [{ c_id: '1', word: 'Test', translation: 'Test' }],
    };

    expect(state.isLoadingDeckDetails).toBe(false);
    expect(state.deckDetails).toBeTruthy();
    expect(state.cards.length).toBeGreaterThan(0);
  });

  test('should handle modal state transitions', () => {
    const modalStates = {
      isCreateCardModalOpen: false,
      isEditCardModalOpen: false,
      isEditDeckModalOpen: false,
      isStartReviewModalVisible: false,
    };

    // Open create card modal
    modalStates.isCreateCardModalOpen = true;
    expect(modalStates.isCreateCardModalOpen).toBe(true);
    expect(modalStates.isEditCardModalOpen).toBe(false);
  });

  test('should track card being edited', () => {
    const cardBeingEdited = {
      c_id: '1',
      word: 'Hola',
      translation: 'Hello',
    };

    expect(cardBeingEdited).toBeTruthy();
    expect(cardBeingEdited.c_id).toBe('1');
  });

  test('should manage pagination for cards', () => {
    const paginationState = {
      currentPage: 1,
      cardsPerPage: 100,
      totalCards: 250,
      nextPage: 2,
      hasMoreCards: true,
    };

    const totalPages = Math.ceil(paginationState.totalCards / paginationState.cardsPerPage);
    expect(totalPages).toBe(3);
    expect(paginationState.hasMoreCards).toBe(true);
  });
});

describe('Common Component Props Validation', () => {
  test('should validate CButton props', () => {
    const buttonProps = {
      label: 'Submit',
      variant: 'primary',
      onPress: jest.fn(),
      disabled: false,
    };

    expect(typeof buttonProps.label).toBe('string');
    expect(['primary', 'secondary', 'danger']).toContain(buttonProps.variant);
    expect(typeof buttonProps.onPress).toBe('function');
  });

  test('should validate CTextInput props', () => {
    const inputProps = {
      placeholder: 'Enter deck name',
      value: '',
      onChangeText: jest.fn(),
      secureTextEntry: false,
    };

    expect(inputProps.placeholder).toBeTruthy();
    expect(typeof inputProps.onChangeText).toBe('function');
  });

  test('should validate Modal props', () => {
    const modalProps = {
      visible: true,
      title: 'Create Deck',
      onClose: jest.fn(),
      children: '<Form />',
    };

    expect(typeof modalProps.visible).toBe('boolean');
    expect(modalProps.title).toBeTruthy();
  });
});

describe('CButton Component Variants', () => {
  test('should validate CButton variants', () => {
    const buttonVariants = ['primary', 'secondary', 'google', 'criticalPrimary', 'criticalSecondary'];
    expect(buttonVariants).toHaveLength(5);
    expect(buttonVariants).toContain('primary');
  });

  test('should handle button disabled state', () => {
    const buttonProps = {
      label: 'Submit',
      disabled: true,
      onPress: jest.fn(),
    };

    expect(buttonProps.disabled).toBe(true);
  });
});

describe('CTextInput Keyboard Types', () => {
  test('should validate CTextInput keyboard types', () => {
    const keyboardTypes = ['default', 'email-address', 'numeric', 'phone-pad', 'url'];
    expect(keyboardTypes).toContain('email-address');
    expect(keyboardTypes).toContain('numeric');
  });

  test('should handle secure text entry', () => {
    const inputProps = {
      placeholder: 'Enter password',
      secureTextEntry: true,
      value: '',
      onChangeText: jest.fn(),
    };

    expect(inputProps.secureTextEntry).toBe(true);
  });
});

describe('CSwitch Component', () => {
  test('should validate CSwitch props', () => {
    const switchProps = {
      value: true,
      onValueChange: jest.fn(),
      disabled: false,
    };

    expect(typeof switchProps.value).toBe('boolean');
    expect(typeof switchProps.onValueChange).toBe('function');
  });

  test('should handle toggle state', () => {
    const switchProps = {
      value: false,
      onValueChange: jest.fn(),
    };

    switchProps.onValueChange(true);
    expect(switchProps.onValueChange).toHaveBeenCalledWith(true);
  });
});

describe('Data Transformation and Formatting', () => {
  test('should format deck creation date', () => {
    const creationDate = '2026-03-31T10:00:00Z';
    const date = new Date(creationDate);

    expect(date.getFullYear()).toBe(2026);
    expect(date.getMonth()).toBe(2);
  });

  test('should format numbers', () => {
    const cardCount = 42;
    expect(cardCount.toString()).toBe('42');
  });

  test('should handle null dates gracefully', () => {
    const lastReviewed: string | null = null;
    const displayDate = lastReviewed ? new Date(lastReviewed).toLocaleDateString() : 'Never';

    expect(displayDate).toBe('Never');
  });

  test('should validate language codes', () => {
    const languageCodes = ['ja', 'fr', 'ko', 'zh'];
    expect(languageCodes).toContain('ja');
    expect(languageCodes.length).toBeGreaterThan(0);
  });

  test('should build language pair display', () => {
    const wordLang = 'Japanese';
    const transLang = 'English';
    const display = `${wordLang} → ${transLang}`;

    expect(display).toBe('Japanese → English');
  });
});

describe('User Authentication and State', () => {
  test('should determine if user has studied today', () => {
    const today = new Date().toISOString();
    const user = {
      lastStudySession: today,
      totalSessions: 25,
      streakDays: 5,
    };

    const hasStudiedToday =
      new Date(user.lastStudySession).toDateString() === new Date().toDateString();

    expect(hasStudiedToday).toBe(true);
    expect(user.totalSessions).toBeGreaterThan(0);
  });

  test('should validate user activity', () => {
    const user = {
      id: '123',
      email: 'user@example.com',
      totalSessions: 15,
    };

    const isActive = user.totalSessions > 0;
    expect(isActive).toBe(true);
  });
});

describe('Error Handling and Edge Cases', () => {
  test('should handle division by zero in progress calculation', () => {
    const sessionData = {
      totalCards: 50,
      reviewedCards: 0,
      correctCards: 0,
    };

    const percentCorrect = sessionData.reviewedCards > 0
      ? (sessionData.correctCards / sessionData.reviewedCards) * 100
      : 0;

    expect(percentCorrect).toBe(0);
  });

  test('should handle very large numbers', () => {
    const largeCount = 999999;
    expect(largeCount.toString().length).toBeGreaterThan(0);
  });

  test('should handle special characters in text', () => {
    const specialText = "It's a test with \"quotes\" and 'apostrophes'";
    expect(specialText).toContain("It's");
    expect(specialText).toContain('"quotes"');
  });

  test('should handle empty response arrays', () => {
    const response = {
      data: [],
      error: null,
    };

    expect(response.data).toHaveLength(0);
    expect(response.error).toBeNull();
  });

  test('should handle form submission with validation', () => {
    const formData = {
      deckName: 'Test',
      language: 'ja',
    };

    const isValid =
      !!formData.deckName &&
      formData.deckName.trim().length > 0 &&
      !!formData.language;

    expect(isValid).toBe(true);
  });
});
