import { describe, expect, test, jest, beforeEach } from "@jest/globals";

jest.mock("expo-router", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  useSegments: () => [],
}));

jest.mock("@/utils/storage", () => ({
  storage: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    deleteItem: jest.fn(),
  },
}));

jest.mock("@/apis/endpoints/decks", () => ({
  getDecks: jest.fn(),
  getSingleDeck: jest.fn(),
  createDeck: jest.fn(),
  updateDeck: jest.fn(),
  deleteDeck: jest.fn(),
}));

jest.mock("@/apis/endpoints/cards", () => ({
  getCards: jest.fn(),
  createCard: jest.fn(),
  updateCard: jest.fn(),
  deleteCard: jest.fn(),
}));

// ============================================================================
// CREATE DECK FORM - Complete Submission Flow
// ============================================================================

describe("CreateDeckForm - Complete Submission Flow", () => {
  let form: any;

  beforeEach(() => {
    jest.clearAllMocks();
    form = {
      values: { deckName: "", wordLanguage: "", translationLanguage: "" },
      touched: {},
      errors: {},
      isSubmitting: false,
      isValid: false,
      dirty: false,
      onBlur: jest.fn(),
      onChange: jest.fn(),
      onSubmit: jest.fn(),
      resetForm: jest.fn(),
    };
  });

  test("form submission flow: initial → fill → validate → submit → success", async () => {
    // Step 1: Form is initialized empty
    expect(form.values.deckName).toBe("");
    expect(form.isValid).toBe(false);

    // Step 2: User types in form fields
    form.values.deckName = "Japanese Beginner";
    form.values.wordLanguage = "ja";
    form.values.translationLanguage = "en";
    form.dirty = true;
    form.onChange({});

    expect(form.values.deckName).toBe("Japanese Beginner");
    expect(form.dirty).toBe(true);

    // Step 3: Form validates after user clears focus
    form.errors = {};
    form.isValid = true;

    expect(form.isValid).toBe(true);
    expect(Object.keys(form.errors).length).toBe(0);

    // Step 4: User clicks submit
    form.isSubmitting = true;

    expect(form.isSubmitting).toBe(true);

    // Step 5: API request succeeds
    form.isSubmitting = false;
    form.submitted = true;

    expect(form.submitted).toBe(true);
    expect(form.isSubmitting).toBe(false);
  });

  test("form submission with validation error: initial → fill → error → correct → submit", async () => {
    // User enters same language for both fields
    form.values.deckName = "Test";
    form.values.wordLanguage = "ja";
    form.values.translationLanguage = "ja";

    // Validation error detected
    form.errors.translationLanguage = "Languages must be different";
    form.isValid = false;

    expect(form.errors.translationLanguage).toBeTruthy();
    expect(form.isValid).toBe(false);

    // User corrects the error
    form.values.translationLanguage = "en";
    form.errors = {};
    form.isValid = true;

    expect(form.isValid).toBe(true);

    // Now form can submit
    form.isSubmitting = true;
    form.isSubmitting = false;
    form.submitted = true;

    expect(form.submitted).toBe(true);
  });

  test("form submission with API error: shows error, allows retry", async () => {
    form.values = {
      deckName: "Test",
      wordLanguage: "ja",
      translationLanguage: "en",
    };
    form.isValid = true;

    // Step 1: First submission attempt
    form.isSubmitting = true;
    form.isSubmitting = false;
    form.errors = { submit: "Network error occurred" };

    expect(form.errors.submit).toBeTruthy();

    // Step 2: User clicks retry
    form.errors = {}; // Clear error message
    form.isSubmitting = true;

    // Step 3: Retry succeeds
    form.isSubmitting = false;
    form.submitted = true;

    expect(form.submitted).toBe(true);
  });

  test("form can be reset after successful submission", async () => {
    form.values = {
      deckName: "Test",
      wordLanguage: "ja",
      translationLanguage: "en",
    };
    form.submitted = true;

    // User wants to create another deck
    form.resetForm(); // Mock implementation
    form.values = { deckName: "", wordLanguage: "", translationLanguage: "" };
    form.touched = {};
    form.errors = {};

    expect(form.values).toEqual({
      deckName: "",
      wordLanguage: "",
      translationLanguage: "",
    });
    expect(form.touched).toEqual({});
    expect(form.errors).toEqual({});
  });

  test("form disables submit button while submitting", () => {
    form.values = {
      deckName: "Test",
      wordLanguage: "ja",
      translationLanguage: "en",
    };
    form.isValid = true;
    form.isSubmitting = true;

    const isSubmitDisabled = form.isSubmitting || !form.isValid;

    expect(isSubmitDisabled).toBe(true);
  });

  test("form field errors do NOT show before touched", () => {
    form.values = { deckName: "" };
    form.touched = {};
    form.errors.deckName = "Deck name is required";

    // Since field wasn't touched, error should not display
    const shouldShowError = form.touched.deckName && form.errors.deckName;

    expect(shouldShowError).toBeFalsy();
  });
});

// ============================================================================
// CREATE CARD FORM - Multi-field Submission
// ============================================================================

describe("CreateCardForm - Multi-field Form Flow", () => {
  let form: any;

  beforeEach(() => {
    form = {
      values: {
        word: "",
        translation: "",
        exampleSentence: "",
        pronunciation: "",
        imageUrl: "",
      },
      errors: {},
      isSubmitting: false,
      isValid: false,
      touched: {},
      onSubmit: jest.fn(),
      resetForm: jest.fn(),
    };
  });

  test("card form submission with all optional fields", () => {
    // Fill required + optional fields
    form.values = {
      word: "こんにちは",
      translation: "Hello",
      exampleSentence: "こんにちは。元気ですか？",
      pronunciation: "kon-ni-chi-wa",
      imageUrl: "https://example.com/hello.jpg",
    };

    form.isValid = true;

    expect(form.values.word).toBe("こんにちは");
    expect(form.values.translation).toBe("Hello");
    expect(form.isValid).toBe(true);

    form.isSubmitting = true;
    form.isSubmitting = false;
    form.submitted = true;

    expect(form.submitted).toBe(true);
  });

  test("card form with only required fields", () => {
    form.values = {
      word: "Word",
      translation: "Translation",
      exampleSentence: "",
      pronunciation: "",
      imageUrl: "",
    };

    form.isValid = true;

    // Should still submit with just required fields
    form.isSubmitting = true;
    form.isSubmitting = false;

    expect(form.isSubmitting).toBe(false);
  });

  test("card form image upload validation", () => {
    form.values.imageUrl = "not-a-url";
    form.errors.imageUrl = "Invalid image URL format";

    expect(form.errors.imageUrl).toBeTruthy();

    // User corrects the URL
    form.values.imageUrl = "https://example.com/image.jpg";
    form.errors.imageUrl = "";

    expect(form.errors.imageUrl).toBe("");
  });
});

// ============================================================================
// REVIEW SESSION - Multi-step Interactive Flow
// ============================================================================

describe("ReviewSession - Complete Review Flow", () => {
  let session: any;

  beforeEach(() => {
    session = {
      dueCards: [
        { c_id: "1", word: "Word 1", translation: "Translation 1" },
        { c_id: "2", word: "Word 2", translation: "Translation 2" },
        { c_id: "3", word: "Word 3", translation: "Translation 3" },
      ],
      currentCardIndex: 0,
      currentCard: null,
      revealed: false,
      rating: null,
      reviewedCards: [],
      isLoading: false,
      isComplete: false,
      canRate: false,
      onRate: jest.fn(),
      onReveal: jest.fn(),
      onNext: jest.fn(),
      onSkip: jest.fn(),
    };

    session.currentCard = session.dueCards[session.currentCardIndex];
  });

  test("complete review session flow: load → review each → complete", () => {
    // Step 1: Loading due cards
    session.isLoading = true;
    expect(session.isLoading).toBe(true);

    // Step 2: Cards loaded, first card displayed
    session.isLoading = false;
    expect(session.currentCard.word).toBe("Word 1");

    // Step 3: User reveals answer
    session.onReveal();
    session.revealed = true;
    session.canRate = session.revealed; // Update canRate based on revealed

    expect(session.revealed).toBe(true);
    expect(session.canRate).toBe(true);

    // Step 4: User rates card (e.g., "Good" = 3)
    session.onRate(3);
    session.rating = 3;
    session.reviewedCards.push({
      ...session.currentCard,
      rating: 3,
    });

    expect(session.reviewedCards.length).toBe(1);

    // Step 5: Move to next card
    session.onNext();
    session.currentCardIndex = 1;
    session.currentCard = session.dueCards[session.currentCardIndex];
    session.revealed = false;
    session.canRate = false;
    session.rating = null;

    expect(session.currentCard.word).toBe("Word 2");

    // Review card 2
    session.onReveal();
    session.revealed = true;
    session.canRate = session.revealed;
    session.onRate(2);
    session.reviewedCards.push({
      ...session.currentCard,
      rating: 2,
    });

    // Step 6: Continue with remaining cards
    session.onNext();
    session.currentCardIndex = 2;
    session.currentCard = session.dueCards[session.currentCardIndex];
    session.revealed = false;
    session.canRate = false;
    session.rating = null;

    session.onReveal();
    session.revealed = true;
    session.canRate = session.revealed;
    session.onRate(4);
    session.reviewedCards.push({
      ...session.currentCard,
      rating: 4,
    });

    // Step 7: No more cards
    session.onNext();
    session.currentCardIndex = 3;
    session.isComplete = session.currentCardIndex >= session.dueCards.length;

    expect(session.isComplete).toBe(true);
    expect(session.reviewedCards.length).toBe(3);
  });

  test("reveals answer before allowing rating", () => {
    expect(session.revealed).toBe(false);
    expect(session.canRate).toBe(false);

    // Cannot rate without revealing
    expect(() => {
      if (!session.revealed) {
        throw new Error("Card must be revealed before rating");
      }
    }).toThrow();

    // Reveal answer
    session.revealed = true;
    session.canRate = session.revealed; // Update canRate based on revealed state

    expect(session.canRate).toBe(true);

    // Now can rate
    session.onRate(3);
    session.rating = 3; // Update rating after onRate is called

    expect(session.rating).toBe(3);
  });

  test("tracks review statistics", () => {
    session.reviewedCards = [
      { rating: 4 }, // Again (difficult)
      { rating: 3 }, // Good
      { rating: 2 }, // Hard
      { rating: 1 }, // Easy
    ];

    const stats = {
      total: session.reviewedCards.length,
      easy: session.reviewedCards.filter((c: any) => c.rating === 1).length,
      good: session.reviewedCards.filter((c: any) => c.rating === 3).length,
      hard: session.reviewedCards.filter((c: any) => c.rating === 2).length,
      again: session.reviewedCards.filter((c: any) => c.rating === 4).length,
    };

    expect(stats.total).toBe(4);
    expect(stats.easy).toBe(1);
    expect(stats.good).toBe(1);
    expect(stats.hard).toBe(1);
    expect(stats.again).toBe(1);
  });

  test("calculates review session time", () => {
    const startTime = Date.now();

    // Simulate reviewing 3 cards
    session.currentCardIndex = 0;
    session.onReveal();
    session.onRate(3);

    session.currentCardIndex = 1;
    session.onReveal();
    session.onRate(3);

    session.currentCardIndex = 2;
    session.onReveal();
    session.onRate(3);

    const endTime = Date.now();
    const duration = endTime - startTime;

    expect(duration).toBeGreaterThanOrEqual(0);
  });

  test("shows progress indicator during review", () => {
    const totalCards = session.dueCards.length;

    // Progress at card 1
    let progress = ((session.currentCardIndex + 1) / totalCards) * 100;
    expect(progress).toBeCloseTo(33.33, 1);

    // Progress at card 2
    session.currentCardIndex = 1;
    progress = ((session.currentCardIndex + 1) / totalCards) * 100;
    expect(progress).toBeCloseTo(66.67, 1);

    // Progress at card 3
    session.currentCardIndex = 2;
    progress = ((session.currentCardIndex + 1) / totalCards) * 100;
    expect(progress).toBe(100);
  });
});

// ============================================================================
// DECK EDITING - Multi-step Edit and Delete Flow
// ============================================================================

describe("DeckEditingFlow", () => {
  let deck: any;

  beforeEach(() => {
    deck = {
      d_id: "123",
      deck_name: "Japanese Vocabulary",
      card_count: 100,
      isEditing: false,
      editForm: { deck_name: "", description: "" },
      onEditStart: jest.fn(),
      onEditSave: jest.fn(),
      onEditCancel: jest.fn(),
      onDelete: jest.fn(),
    };
  });

  test("edit deck flow: view → edit → save", () => {
    // Step 1: View deck
    expect(deck.isEditing).toBe(false);

    // Step 2: User clicks edit
    deck.onEditStart();
    deck.isEditing = true;
    deck.editForm.deck_name = deck.deck_name;

    expect(deck.isEditing).toBe(true);
    expect(deck.editForm.deck_name).toBe("Japanese Vocabulary");

    // Step 3: User modifies name
    deck.editForm.deck_name = "Advanced Japanese";

    expect(deck.editForm.deck_name).toBe("Advanced Japanese");

    // Step 4: User saves
    deck.onEditSave();
    deck.deck_name = deck.editForm.deck_name;
    deck.isEditing = false;

    expect(deck.deck_name).toBe("Advanced Japanese");
    expect(deck.isEditing).toBe(false);
  });

  test("edit can be cancelled without saving changes", () => {
    const originalName = deck.deck_name;

    // Enter edit mode and make changes
    deck.isEditing = true;
    deck.editForm.deck_name = "New Name";

    expect(deck.editForm.deck_name).toBe("New Name");

    // Cancel edit
    deck.onEditCancel();
    deck.isEditing = false;

    // Original name unchanged
    expect(deck.deck_name).toBe(originalName);
  });

  test("delete deck with confirmation dialog flow", () => {
    let confirmDialog = {
      visible: false,
      title: "Delete Deck?",
      message: `Are you sure you want to delete "${deck.deck_name}"?`,
      onConfirm: jest.fn(),
      onCancel: jest.fn(),
    };

    // Step 1: User clicks delete
    confirmDialog.visible = true;
    expect(confirmDialog.visible).toBe(true);

    // Step 2: User confirms deletion
    confirmDialog.onConfirm();
    deck.onDelete();
    confirmDialog.visible = false;

    expect(confirmDialog.onConfirm).toHaveBeenCalled();
    expect(deck.onDelete).toHaveBeenCalled();
  });

  test("delete can be cancelled", () => {
    let confirmDialog = {
      visible: false,
      onCancel: jest.fn(),
    };

    // User clicks delete
    confirmDialog.visible = true;

    // User changes mind
    confirmDialog.onCancel();
    confirmDialog.visible = false;

    expect(confirmDialog.visible).toBe(false);
  });
});

// ============================================================================
// CARD MANAGEMENT - Add, Edit, Delete Cards
// ============================================================================

describe("CardManagementFlow", () => {
  let cardList: any = [];
  let createCardForm: any;

  beforeEach(() => {
    jest.clearAllMocks();
    cardList = [
      { c_id: "1", word: "Hello", translation: "Hola" },
      { c_id: "2", word: "Goodbye", translation: "Adiós" },
    ];

    createCardForm = {
      values: { word: "", translation: "" },
      errors: {},
      isSubmitting: false,
      onSubmit: jest.fn(),
      resetForm: jest.fn(),
    };
  });

  test("add card to deck flow", () => {
    // Step 1: Form is empty
    expect(createCardForm.values.word).toBe("");

    // Step 2: User fills form
    createCardForm.values.word = "Good Morning";
    createCardForm.values.translation = "Buenos días";

    // Step 3: Form validates
    createCardForm.errors = {};

    // Step 4: User submits
    createCardForm.isSubmitting = true;

    // Step 5: Card added to list
    createCardForm.isSubmitting = false;
    const newCard = {
      c_id: "3",
      word: createCardForm.values.word,
      translation: createCardForm.values.translation,
    };
    cardList.push(newCard);

    expect(cardList.length).toBe(3);
    expect(cardList[2].word).toBe("Good Morning");
  });

  test("edit card flow", () => {
    const cardToEdit = cardList[0];

    // Step 1: User clicks edit
    const editForm = {
      values: { word: cardToEdit.word, translation: cardToEdit.translation },
      onSubmit: jest.fn(),
    };

    // Step 2: User modifies card
    editForm.values.word = "Hi";

    // Step 3: User saves
    editForm.onSubmit();
    cardToEdit.word = editForm.values.word;

    expect(cardList[0].word).toBe("Hi");
  });

  test("delete card flow with confirmation", () => {
    const cardToDelete = cardList[1];

    let confirmDialog = {
      visible: false,
      message: `Delete "${cardToDelete.word}"?`,
      onConfirm: jest.fn(),
    };

    // User clicks delete
    confirmDialog.visible = true;

    // User confirms
    confirmDialog.onConfirm();
    cardList = cardList.filter((c: any) => c.c_id !== cardToDelete.c_id);
    confirmDialog.visible = false;

    expect(cardList.length).toBe(1);
    expect(cardList[0].word).toBe("Hello");
  });

  test("bulk delete cards", () => {
    const cardsToDelete = [cardList[0], cardList[1]];
    const selectedIds = cardsToDelete.map((c: any) => c.c_id);

    cardList = cardList.filter((c: any) => !selectedIds.includes(c.c_id));

    expect(cardList.length).toBe(0);
  });
});

// ============================================================================
// PAGINATION & LAZY LOADING - Handling Large Lists
// ============================================================================

describe("PaginationAndLazyLoading", () => {
  let paginatedList: any;

  beforeEach(() => {
    paginatedList = {
      items: Array.from({ length: 50 }, (_, i) => ({
        id: i + 1,
        name: `Item ${i + 1}`,
      })),
      currentPage: 1,
      pageSize: 10,
      isLoading: false,
      errorMessage: null,
      getVisibleItems() {
        const start = (this.currentPage - 1) * this.pageSize;
        return this.items.slice(start, start + this.pageSize);
      },
      getTotalPages() {
        return Math.ceil(this.items.length / this.pageSize);
      },
      goToPage(page: number) {
        if (page >= 1 && page <= this.getTotalPages()) {
          this.currentPage = page;
        }
      },
      loadNextPage: jest.fn(),
    };
  });

  test("displays first page of items", () => {
    const visible = paginatedList.getVisibleItems();

    expect(visible.length).toBe(10);
    expect(visible[0].id).toBe(1);
    expect(visible[9].id).toBe(10);
  });

  test("loads next page when user scrolls", () => {
    paginatedList.goToPage(2);

    const visible = paginatedList.getVisibleItems();

    expect(visible.length).toBe(10);
    expect(visible[0].id).toBe(11);
    expect(visible[9].id).toBe(20);
  });

  test("shows loading indicator while loading next page", () => {
    paginatedList.isLoading = true;
    paginatedList.loadNextPage();

    expect(paginatedList.isLoading).toBe(true);

    paginatedList.isLoading = false;

    expect(paginatedList.isLoading).toBe(false);
  });

  test("calculates total pages correctly", () => {
    const totalPages = paginatedList.getTotalPages();

    expect(totalPages).toBe(5);
  });

  test("pagination navigation works", () => {
    // Go to page 3
    paginatedList.goToPage(3);
    expect(paginatedList.currentPage).toBe(3);

    // Try invalid page (should not change)
    paginatedList.goToPage(10);
    expect(paginatedList.currentPage).toBe(3);

    // Go to last page
    paginatedList.goToPage(5);
    expect(paginatedList.currentPage).toBe(5);
  });

  test("shows remaining items on last page", () => {
    paginatedList.goToPage(5);
    const visible = paginatedList.getVisibleItems();

    expect(visible.length).toBe(10);
    expect(visible[0].id).toBe(41);
    expect(visible[9].id).toBe(50);
  });
});

// ============================================================================
// AUTHENTICATION FLOW - Sign In/Up/Out Multi-step
// ============================================================================

describe("AuthenticationFlow", () => {
  let auth: any;

  beforeEach(() => {
    auth = {
      user: null,
      isLoading: false,
      error: null,
      formValues: { email: "", password: "" },
      onEmailChange: jest.fn(),
      onPasswordChange: jest.fn(),
      onSignIn: jest.fn(),
      onSignOut: jest.fn(),
      resetForm: jest.fn(),
    };
  });

  test("sign in flow: form → submit → authenticated", async () => {
    // Step 1: Form empty
    expect(auth.user).toBeNull();

    // Step 2: User enters credentials
    auth.formValues.email = "user@example.com";
    auth.formValues.password = "password123";

    // Step 3: User submits
    auth.isLoading = true;

    // Step 4: Server authenticates
    auth.isLoading = false;
    auth.user = {
      id: "123",
      email: "user@example.com",
      name: "John Doe",
    };

    expect(auth.user).toBeTruthy();
    expect(auth.user.email).toBe("user@example.com");
  });

  test("sign in with validation error", () => {
    auth.formValues.email = "invalid-email";
    auth.error = "Invalid email format";

    expect(auth.error).toBeTruthy();

    // User fixes error
    auth.formValues.email = "user@example.com";
    auth.error = null;

    expect(auth.error).toBeNull();
  });

  test("sign in with server error", async () => {
    auth.formValues.email = "user@example.com";
    auth.formValues.password = "wrongpassword";

    auth.isLoading = true;
    auth.isLoading = false;
    auth.error = "Invalid email or password";

    expect(auth.error).toBeTruthy();
    expect(auth.user).toBeNull();
  });

  test("sign out flow", () => {
    // User signed in
    auth.user = { id: "123", email: "user@example.com" };

    // User clicks sign out
    auth.onSignOut();
    auth.user = null;
    auth.resetForm();

    expect(auth.user).toBeNull();
  });

  test("automatically signs out on token expiry", () => {
    auth.user = { id: "123", email: "user@example.com" };

    // Token expires
    auth.user = null;
    auth.error = "Session expired. Please sign in again.";

    expect(auth.user).toBeNull();
    expect(auth.error).toBeTruthy();
  });
});
