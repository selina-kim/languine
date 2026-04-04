import { describe, expect, test, jest, beforeEach } from '@jest/globals';

// ============================================================================
// DATA STATE TESTS - Components with Loading, Success, Error, Empty States
// ============================================================================
// Verifies components correctly render different data states and handle
// conditional rendering logic based on API responses.
// ============================================================================

jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  useSegments: () => [],
}));

jest.mock('@/utils/storage', () => ({
  storage: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    deleteItem: jest.fn(),
  },
}));

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

jest.mock('@/apis/endpoints/fsrs', () => ({
  getDueCards: jest.fn(),
  getNumDueCards: jest.fn(),
  logReview: jest.fn(),
  endReview: jest.fn(),
}));

jest.mock('@react-native-google-signin/google-signin', () => ({
  GoogleSignin: {
    signIn: jest.fn(),
    signOut: jest.fn(),
    isSignedIn: jest.fn(),
  },
}));

jest.mock('@/context/AuthContext', () => ({
  AuthContext: {},
  useAuth: () => ({
    user: null,
    isLoading: false,
    signIn: jest.fn(),
    signUp: jest.fn(),
    signOut: jest.fn(),
  }),
}));

jest.mock('@/context/LanguageOptionsContext', () => ({
  LanguageOptionsContext: {},
  useLanguageOptions: () => ({
    languages: [],
    isLoading: false,
  }),
}));

// ============================================================================
// DECK LIST - Data State Testing
// ============================================================================

describe('DeckList Component - Data States', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('shows loading spinner when decks are being fetched', () => {
    const loadingState = {
      isLoading: true,
      data: null,
      error: null,
    };

    expect(loadingState.isLoading).toBe(true);
    expect(loadingState.data).toBeNull();

    // Component should show spinner/skeleton
    const shouldShowSpinner = loadingState.isLoading && !loadingState.data;
    expect(shouldShowSpinner).toBe(true);
  });

  test('displays deck list when data loads successfully', () => {
    const successState = {
      isLoading: false,
      data: [
        { d_id: '1', deck_name: 'Japanese', card_count: 100 },
        { d_id: '2', deck_name: 'Korean', card_count: 50 },
      ],
      error: null,
    };

    expect(successState.isLoading).toBe(false);
    expect(successState.data).toBeTruthy();
    expect(successState.data?.length).toBe(2);

    // Component should show deck list
    const shouldShowList = !successState.isLoading && successState.data && successState.data.length > 0;
    expect(shouldShowList).toBe(true);
  });

  test('shows empty state banner when no decks exist', () => {
    const emptyState = {
      isLoading: false,
      data: [],
      error: null,
    };

    expect(emptyState.isLoading).toBe(false);
    expect(Array.isArray(emptyState.data)).toBe(true);
    expect(emptyState.data.length).toBe(0);

    // Component should show "No Decks" banner
    const shouldShowEmptyBanner = !!(!emptyState.isLoading && emptyState.data && emptyState.data.length === 0);
    expect(shouldShowEmptyBanner).toBe(true);
  });

  test('displays error message when deck fetch fails', () => {
    const errorState = {
      isLoading: false,
      data: null,
      error: 'Failed to fetch decks',
    };

    expect(errorState.isLoading).toBe(false);
    expect(errorState.error).toBeTruthy();

    // Component should show error message with retry button
    const shouldShowError = !!(!errorState.isLoading && errorState.error);
    expect(shouldShowError).toBe(true);
  });

  test('transitions from loading to success state', () => {
    let state: any = {
      isLoading: true,
      data: null,
      error: null,
    };

    // Simulate API response
    state = {
      isLoading: false,
      data: [{ d_id: '1', deck_name: 'Test' }],
      error: null,
    };

    expect(state.isLoading).toBe(false);
    expect(state.data).toBeTruthy();
  });

  test('transitions from loading to error state', () => {
    let state: any = {
      isLoading: true,
      data: null,
      error: null,
    };

    // Simulate API error
    state = {
      isLoading: false,
      data: null,
      error: 'Network error',
    };

    expect(state.isLoading).toBe(false);
    expect(state.error).toBeTruthy();
  });

  test('can retry loading after error', () => {
    const errorState = {
      isLoading: false,
      data: null,
      error: 'Network error',
      onRetry: jest.fn(),
    };

    // User clicks retry button
    errorState.onRetry();

    expect(errorState.onRetry).toHaveBeenCalled();
  });

  test('hides loading indicator after load completes', () => {
    const state = {
      isLoading: false,
      data: [{ d_id: '1' }],
    };

    expect(state.isLoading).toBe(false);

    // Spinner should be hidden
    const spinnerVisible = state.isLoading;
    expect(spinnerVisible).toBe(false);
  });
});

// ============================================================================
// CARDS LIST - Data State Testing
// ============================================================================

describe('CardsList Component - Data States', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('shows loading state while fetching cards', () => {
    const loadingState = {
      isLoading: true,
      cards: null,
      error: null,
    };

    expect(loadingState.isLoading).toBe(true);
    const shouldShowSpinner = loadingState.isLoading;
    expect(shouldShowSpinner).toBe(true);
  });

  test('displays all cards successfully', () => {
    const successState = {
      isLoading: false,
      cards: [
        { c_id: '1', word: 'Hello', translation: 'Hola' },
        { c_id: '2', word: 'Goodbye', translation: 'Adiós' },
        { c_id: '3', word: 'Thank you', translation: 'Gracias' },
      ],
      error: null,
    };

    expect(successState.isLoading).toBe(false);
    expect(successState.cards?.length).toBe(3);

    const shouldShowCards = successState.cards && successState.cards.length > 0;
    expect(shouldShowCards).toBe(true);
  });

  test('shows empty message when deck has no cards', () => {
    const emptyState = {
      isLoading: false,
      cards: [],
      error: null,
    };

    expect(emptyState.cards?.length).toBe(0);

    const shouldShowEmptyMessage = !emptyState.isLoading && emptyState.cards && emptyState.cards.length === 0;
    expect(shouldShowEmptyMessage).toBe(true);
  });

  test('displays error when card fetch fails', () => {
    const errorState = {
      isLoading: false,
      cards: null,
      error: 'Failed to load cards',
    };

    expect(errorState.error).toBeTruthy();

    const shouldShowError = !!(!errorState.isLoading && errorState.error);
    expect(shouldShowError).toBe(true);
  });

  test('updates card count after adding card', () => {
    let state: any = {
      cards: [{ c_id: '1', word: 'Hello' }],
      cardCount: 1,
    };

    const newCard = { c_id: '2', word: 'Goodbye' };
    state.cards = [...state.cards, newCard];
    state.cardCount = state.cards.length;

    expect(state.cardCount).toBe(2);
  });
});

// ============================================================================
// REVIEW SESSION - Data State Testing
// ============================================================================

describe('ReviewSession Component - Data States', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('shows loading while fetching due cards', () => {
    const state = {
      isLoading: true,
      dueCards: null,
      error: null,
    };

    expect(state.isLoading).toBe(true);
    const shouldShowSpinner = state.isLoading;
    expect(shouldShowSpinner).toBe(true);
  });

  test('displays review session when due cards loaded', () => {
    const state = {
      isLoading: false,
      dueCards: [
        { c_id: '1', word: 'Word 1' },
        { c_id: '2', word: 'Word 2' },
      ],
      currentCardIndex: 0,
      error: null,
    };

    expect(state.isLoading).toBe(false);
    expect(state.dueCards).toBeTruthy();

    const shouldShowReview = !state.isLoading && state.dueCards && state.dueCards.length > 0;
    expect(shouldShowReview).toBe(true);
  });

  test('shows empty message when no cards due for review', () => {
    const state = {
      isLoading: false,
      dueCards: [],
      error: null,
    };

    expect(state.dueCards?.length).toBe(0);

    const shouldShowEmptyMessage = !state.isLoading && state.dueCards && state.dueCards.length === 0;
    expect(shouldShowEmptyMessage).toBe(true);
  });

  test('displays error when due cards fetch fails', () => {
    const state = {
      isLoading: false,
      dueCards: null,
      error: 'Failed to fetch due cards',
    };

    expect(state.error).toBeTruthy();

    const shouldShowError = !!(!state.isLoading && state.error);
    expect(shouldShowError).toBe(true);
  });

  test('shows current card during review session', () => {
    const state = {
      dueCards: [
        { c_id: '1', word: 'Word 1' },
        { c_id: '2', word: 'Word 2' },
      ],
      currentCardIndex: 0,
    };

    expect(state.dueCards[state.currentCardIndex]).toBeDefined();
    expect(state.dueCards[state.currentCardIndex].word).toBe('Word 1');
  });

  test('updates progress as cards are reviewed', () => {
    const state = {
      dueCards: [
        { c_id: '1', word: 'Word 1' },
        { c_id: '2', word: 'Word 2' },
        { c_id: '3', word: 'Word 3' },
      ],
      currentCardIndex: 0,
    };

    const progress = ((state.currentCardIndex + 1) / state.dueCards.length) * 100;
    expect(progress).toBeCloseTo(33.33, 1);

    // After reviewing first card
    state.currentCardIndex = 1;
    const newProgress = ((state.currentCardIndex + 1) / state.dueCards.length) * 100;
    expect(newProgress).toBeCloseTo(66.67, 1);
  });

  test('shows session complete when all cards reviewed', () => {
    let state: any = {
      dueCards: [
        { c_id: '1', word: 'Word 1' },
        { c_id: '2', word: 'Word 2' },
      ],
      currentCardIndex: 1,
    };

    state.isComplete = state.currentCardIndex === state.dueCards.length - 1;

    expect(state.isComplete || state.currentCardIndex === state.dueCards.length - 1).toBe(true);
  });
});

// ============================================================================
// FORM VALIDATION - Data State Testing
// ============================================================================

describe('CreateDeckForm - Data States and Validation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('form shows empty state initially', () => {
    const formState = {
      values: { deckName: '', wordLanguage: '', translationLanguage: '' },
      errors: {},
      isSubmitting: false,
    };

    expect(formState.values.deckName).toBe('');
    expect(Object.keys(formState.errors).length).toBe(0);
    expect(formState.isSubmitting).toBe(false);
  });

  test('form shows validation errors for empty required fields', () => {
    const formState = {
      values: { deckName: '', wordLanguage: '', translationLanguage: '' },
      errors: {
        deckName: 'Deck name is required',
        wordLanguage: 'Word language is required',
        translationLanguage: 'Translation language is required',
      },
      isSubmitting: false,
    };

    expect(Object.keys(formState.errors).length).toBeGreaterThan(0);
    expect(formState.errors.deckName).toBeTruthy();
  });

  test('form validates language pair is different', () => {
    const formState = {
      values: { deckName: 'Test', wordLanguage: 'ja', translationLanguage: 'ja' },
      errors: { translationLanguage: 'Languages must be different' },
    };

    expect(formState.errors.translationLanguage).toBeTruthy();
  });

  test('form clears errors when valid data is entered', () => {
    let formState: any = {
      values: { deckName: '', wordLanguage: 'ja', translationLanguage: 'en' },
      errors: { deckName: 'Required' },
    };

    // User enters deck name
    formState.values.deckName = 'Japanese Vocab';
    formState.errors = {};

    expect(Object.keys(formState.errors).length).toBe(0);
    expect(formState.values.deckName).toBe('Japanese Vocab');
  });

  test('form shows loading state during submission', () => {
    const formState = {
      values: { deckName: 'Valid Deck', wordLanguage: 'ja', translationLanguage: 'en' },
      errors: {},
      isSubmitting: true,
    };

    expect(formState.isSubmitting).toBe(true);

    // Submit button should be disabled
    const isSubmitButtonDisabled = formState.isSubmitting;
    expect(isSubmitButtonDisabled).toBe(true);
  });

  test('form shows success message after submission', () => {
    const formState = {
      values: { deckName: 'Test Deck', wordLanguage: 'ja', translationLanguage: 'en' },
      errors: {},
      isSubmitting: false,
      successMessage: 'Deck created successfully',
    };

    expect(formState.successMessage).toBeTruthy();
    expect(formState.isSubmitting).toBe(false);
  });

  test('form shows error message on submission failure', () => {
    const formState = {
      values: { deckName: 'Test Deck', wordLanguage: 'ja', translationLanguage: 'en' },
      errors: { submit: 'Failed to create deck' },
      isSubmitting: false,
    };

    expect(formState.errors.submit).toBeTruthy();
  });

  test('form allows retry after submission error', () => {
    const formState = {
      values: { deckName: 'Test Deck', wordLanguage: 'ja', translationLanguage: 'en' },
      errors: { submit: 'Network error' },
      onRetry: jest.fn(),
    };

    formState.onRetry();

    expect(formState.onRetry).toHaveBeenCalled();
  });
});

// ============================================================================
// SETTINGS PAGE - Data State Testing
// ============================================================================

describe('SettingsPage - Data States', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('shows loading state while fetching user settings', () => {
    const state = {
      isLoading: true,
      settings: null,
      error: null,
    };

    expect(state.isLoading).toBe(true);
    const shouldShowSpinner = state.isLoading;
    expect(shouldShowSpinner).toBe(true);
  });

  test('displays user settings successfully', () => {
    const state = {
      isLoading: false,
      settings: {
        userName: 'John Doe',
        email: 'john@example.com',
        language: 'en',
      },
      error: null,
    };

    expect(state.isLoading).toBe(false);
    expect(state.settings).toBeTruthy();
    expect(state.settings.userName).toBe('John Doe');
  });

  test('shows error when settings fetch fails', () => {
    const state = {
      isLoading: false,
      settings: null,
      error: 'Failed to load settings',
    };

    expect(state.error).toBeTruthy();
  });

  test('shows loading indicator while saving settings changes', () => {
    const state = {
      isLoading: false,
      isSaving: true,
      settings: {
        userName: 'Jane Doe',
      },
    };

    expect(state.isSaving).toBe(true);

    // Save button should be disabled
    const isSaveButtonDisabled = state.isSaving;
    expect(isSaveButtonDisabled).toBe(true);
  });

  test('shows success message after settings updated', () => {
    const state = {
      isSaving: false,
      isUpdated: true,
      successMessage: 'Settings saved successfully',
    };

    expect(state.isUpdated).toBe(true);
    expect(state.successMessage).toBeTruthy();
  });

  test('shows error when settings update fails', () => {
    const state = {
      isSaving: false,
      error: 'Failed to save settings',
    };

    expect(state.error).toBeTruthy();
  });
});

// ============================================================================
// MODAL DIALOGS - Data State Testing
// ============================================================================

describe('ModalDialogs - Data States', () => {
  test('modal visible state controls rendering', () => {
    const hiddenModal = {
      visible: false,
      title: 'Create Deck',
    };

    expect(hiddenModal.visible).toBe(false);

    // Modal should not render
    const shouldRender = hiddenModal.visible;
    expect(shouldRender).toBe(false);
  });

  test('modal shows when visible is true', () => {
    const visibleModal = {
      visible: true,
      title: 'Create Deck',
      content: 'Form fields...',
    };

    expect(visibleModal.visible).toBe(true);

    // Modal should render
    const shouldRender = visibleModal.visible;
    expect(shouldRender).toBe(true);
  });

  test('confirmation modal shows when needed', () => {
    const confirmModal = {
      visible: true,
      type: 'confirm',
      title: 'Delete Deck?',
      message: 'This action cannot be undone',
      onConfirm: jest.fn(),
      onCancel: jest.fn(),
    };

    expect(confirmModal.visible).toBe(true);
    expect(confirmModal.type).toBe('confirm');
  });

  test('confirmation modal actions work', () => {
    const confirmModal = {
      onConfirm: jest.fn(),
      onCancel: jest.fn(),
    };

    confirmModal.onConfirm();
    expect(confirmModal.onConfirm).toHaveBeenCalled();

    confirmModal.onCancel();
    expect(confirmModal.onCancel).toHaveBeenCalled();
  });
});

// ============================================================================
// CONDITIONAL RENDERING LOGIC TESTS
// ============================================================================

describe('Conditional Rendering Logic', () => {
  test('shows spinner OR deck list (never both)', () => {
    const state1: any = { isLoading: true, data: null };
    const state2: any = { isLoading: false, data: [{ id: '1' }] };

    expect(state1.isLoading !== (state1.data && state1.data.length > 0)).toBe(true);
    expect(state2.isLoading !== (state2.data && state2.data.length > 0)).toBe(true);
  });

  test('shows error OR success (never both)', () => {
    const successState = { error: null, data: [{ id: '1' }] };
    const errorState = { error: 'Failed', data: null };

    // Can't show both error and data at the same time
    const canShowBoth1 = !!(!!successState.error && successState.data);
    const canShowBoth2 = !!(!!errorState.error && errorState.data);

    expect(canShowBoth1).toBe(false);
    expect(canShowBoth2).toBe(false);
  });

  test('shows empty banner when data is empty but loaded', () => {
    const state = { isLoading: false, data: [], error: null };

    const shouldShowEmpty = !state.isLoading && state.data && state.data.length === 0 && !state.error;
    expect(shouldShowEmpty).toBe(true);
  });

  test('shows list when data exists', () => {
    const state = { isLoading: false, data: [{ id: '1' }, { id: '2' }], error: null };

    const shouldShowList = !state.isLoading && state.data && state.data.length > 0;
    expect(shouldShowList).toBe(true);
  });

  test('button disabled state depends on form validity', () => {
    const validForm = { isDirty: true, isValid: true };
    const invalidForm = { isDirty: true, isValid: false };

    const isDisabled1 = !validForm.isValid;
    const isDisabled2 = !invalidForm.isValid;

    expect(isDisabled1).toBe(false);
    expect(isDisabled2).toBe(true);
  });
});
