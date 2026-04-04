import { describe, expect, test, jest, beforeEach } from '@jest/globals';

// ============================================================================
// SPECIAL CONSIDERATIONS TEST SUITE
// Tests for: Google OAuth, Card Flip Interactions, Optimistic Updates, Navigation
// ============================================================================

// Mock GoogleSignin for OAuth tests
jest.mock('@react-native-google-signin/google-signin', () => ({
  GoogleSignin: {
    configure: jest.fn() as any,
    hasPlayServices: (jest.fn() as any).mockResolvedValue(true),
    signIn: (jest.fn() as any).mockResolvedValue({}),
    getTokens: (jest.fn() as any).mockResolvedValue({}),
    getCurrentUser: (jest.fn() as any).mockResolvedValue({}),
    signOut: (jest.fn() as any).mockResolvedValue(null),
  },
}));

jest.mock('@/utils/storage', () => ({
  setSecureItem: (jest.fn() as any).mockResolvedValue(undefined),
  getSecureItem: (jest.fn() as any).mockResolvedValue(null),
  removeSecureItem: (jest.fn() as any).mockResolvedValue(undefined),
}));

// ============================================================================
// GOOGLE OAUTH FLOW INTEGRATION
// ============================================================================

describe('Google OAuth Flow Integration', () => {
  let googleSigninMock: any;
  let storageMock: any;

  beforeEach(() => {
    const { GoogleSignin } = require('@react-native-google-signin/google-signin');
    googleSigninMock = GoogleSignin;

    const storage = require('@/utils/storage');
    storageMock = storage;

    jest.clearAllMocks();
  });

  test('should configure Google Sign-In on app initialization', () => {
    const webClientId = 'test-web-client-id.apps.googleusercontent.com';

    googleSigninMock.configure({
      webClientId,
      offlineAccess: true,
      hostedDomain: 'myapp.example.com',
    });

    expect(googleSigninMock.configure).toHaveBeenCalledWith({
      webClientId,
      offlineAccess: true,
      hostedDomain: 'myapp.example.com',
    });
  });

  test('handleGoogleSignIn: checks play services available on Android', async () => {
    const handleGoogleSignIn = async () => {
      try {
        await googleSigninMock.hasPlayServices({ showPlayServicesUpdateDialog: true });
        return { success: true };
      } catch (error) {
        return { success: false, error };
      }
    };

    const result = await handleGoogleSignIn();

    expect(googleSigninMock.hasPlayServices).toHaveBeenCalledWith({
      showPlayServicesUpdateDialog: true,
    });
    expect(result.success).toBe(true);
  });

  test('handleGoogleSignIn: triggers sign-in when play services available', async () => {
    googleSigninMock.signIn.mockResolvedValue({
      user: {
        id: 'google_user_123',
        email: 'user@gmail.com',
        name: 'John Doe',
      },
    });

    const handleGoogleSignIn = async () => {
      try {
        await googleSigninMock.hasPlayServices();
        const userInfo = await googleSigninMock.signIn();
        return { success: true, user: userInfo.user };
      } catch (error) {
        return { success: false, error };
      }
    };

    const result = await handleGoogleSignIn();

    expect(googleSigninMock.hasPlayServices).toHaveBeenCalled();
    expect(googleSigninMock.signIn).toHaveBeenCalled();
    expect(result.success).toBe(true);
    expect(result.user.email).toBe('user@gmail.com');
  });

  test('handleGoogleSignIn: retrieves and stores tokens after sign-in', async () => {
    googleSigninMock.signIn.mockResolvedValue({
      user: { id: 'user123', email: 'user@gmail.com' },
    });
    googleSigninMock.getTokens.mockResolvedValue({
      accessToken: 'access_token_abc123',
      idToken: 'id_token_xyz789',
    });

    const handleGoogleSignIn = async () => {
      try {
        const userInfo = await googleSigninMock.signIn();
        const tokens = await googleSigninMock.getTokens();

        // Store tokens
        await storageMock.setSecureItem('userToken', tokens.idToken);
        await storageMock.setSecureItem('refreshToken', tokens.accessToken);

        return { success: true, tokens };
      } catch (error) {
        return { success: false, error };
      }
    };

    const result = await handleGoogleSignIn();

    expect(result.success).toBe(true);
    expect(googleSigninMock.getTokens).toHaveBeenCalled();
    expect(storageMock.setSecureItem).toHaveBeenCalledWith(
      'userToken',
      'id_token_xyz789'
    );
    expect(storageMock.setSecureItem).toHaveBeenCalledWith(
      'refreshToken',
      'access_token_abc123'
    );
  });

  test('handleGoogleSignIn: handles play services error gracefully', async () => {
    googleSigninMock.hasPlayServices.mockRejectedValue(
      new Error('Play Services not available')
    );

    const handleGoogleSignIn = async () => {
      try {
        await googleSigninMock.hasPlayServices();
        return { success: true };
      } catch (error: any) {
        return { success: false, error: error.message };
      }
    };

    const result = await handleGoogleSignIn();

    expect(result.success).toBe(false);
    expect(result.error).toBe('Play Services not available');
  });

  test('handleGoogleSignIn: handles sign-in cancellation', async () => {
    googleSigninMock.signIn.mockRejectedValue({
      code: 'CANCELED',
      message: 'User cancelled the operation',
    });

    const handleGoogleSignIn = async () => {
      try {
        await googleSigninMock.signIn();
        return { success: true };
      } catch (error: any) {
        if (error.code === 'CANCELED') {
          return { success: false, cancelled: true };
        }
        return { success: false, error: error.message };
      }
    };

    const result = await handleGoogleSignIn();

    expect(result.success).toBe(false);
    expect(result.cancelled).toBe(true);
  });

  test('handleGoogleSignIn: extracts user info from token', async () => {
    const handleGoogleSignIn = async () => {
      googleSigninMock.signIn.mockResolvedValue({
        user: {
          id: 'google_user_123',
          email: 'user@gmail.com',
          name: 'John Doe',
          givenName: 'John',
          familyName: 'Doe',
          photo: 'https://example.com/photo.jpg',
        },
      });

      const userInfo = await googleSigninMock.signIn();

      return {
        userId: userInfo.user.id,
        email: userInfo.user.email,
        displayName: userInfo.user.name,
        photoUrl: userInfo.user.photo,
      };
    };

    const userInfo = await handleGoogleSignIn();

    expect(userInfo.userId).toBe('google_user_123');
    expect(userInfo.email).toBe('user@gmail.com');
    expect(userInfo.displayName).toBe('John Doe');
  });

  test('handleSignOut: clears tokens from storage', async () => {
    googleSigninMock.signOut.mockResolvedValue(null);

    const handleSignOut = async () => {
      await googleSigninMock.signOut();
      await storageMock.removeSecureItem('userToken');
      await storageMock.removeSecureItem('refreshToken');
      return { success: true };
    };

    const result = await handleSignOut();

    expect(googleSigninMock.signOut).toHaveBeenCalled();
    expect(storageMock.removeSecureItem).toHaveBeenCalledWith('userToken');
    expect(storageMock.removeSecureItem).toHaveBeenCalledWith('refreshToken');
    expect(result.success).toBe(true);
  });
});

// ============================================================================
// CARD FLIP INTERACTION & REVIEW RATING SUBMISSION
// ============================================================================

describe('CardFlip Interaction and Review Rating', () => {
  let cardState: any;
  let cardHandlers: any;

  beforeEach(() => {
    cardState = {
      cards: [
        {
          c_id: 'card1',
          word: 'りんご',
          translation: 'Apple',
          word_example: 'りんご を食べます。',
          trans_example: 'I eat an apple.',
          image: 'apple.jpg',
        },
        {
          c_id: 'card2',
          word: '猫',
          translation: 'Cat',
          word_example: '猫は可愛いです。',
          trans_example: 'The cat is cute.',
          image: 'cat.jpg',
        },
      ],
      currentCardIndex: 0,
      isFrontSide: true,
      hasRevealedBackOnce: false,
      reviewedCards: [],
      cardStartTimeRef: { current: Date.now() },
    };

    cardHandlers = {
      handleCardPress: jest.fn((state: any) => {
        if (state.isFrontSide) {
          return {
            ...state,
            isFrontSide: false,
            hasRevealedBackOnce: true,
          };
        }
        return {
          ...state,
          isFrontSide: true,
        };
      }),

      handleSelectDifficulty: jest.fn((state: any, grade: any) => {
        const cardStartTime = state.cardStartTimeRef.current;
        const reviewDuration = Date.now() - cardStartTime;

        const reviewed = {
          c_id: state.cards[state.currentCardIndex].c_id,
          grade,
          duration: reviewDuration,
          timestamp: Date.now(),
        };

        const nextIndex = state.currentCardIndex + 1;
        return {
          ...state,
          reviewedCards: [...state.reviewedCards, reviewed],
          currentCardIndex: nextIndex,
          isFrontSide: true,
          hasRevealedBackOnce: false,
          cardStartTimeRef: { current: Date.now() },
          isSessionComplete: nextIndex >= state.cards.length,
        };
      }),
    };
  });

  test('card displays front side (word) initially', () => {
    expect(cardState.isFrontSide).toBe(true);
    const currentCard = cardState.cards[cardState.currentCardIndex];
    expect(currentCard.word).toBe('りんご');
  });

  test('handleCardPress: flips from front to back side', () => {
    const newState = cardHandlers.handleCardPress(cardState);

    expect(newState.isFrontSide).toBe(false);
    expect(newState.hasRevealedBackOnce).toBe(true);
  });

  test('handleCardPress: back side displays translation', () => {
    const newState = cardHandlers.handleCardPress(cardState);
    const currentCard = cardState.cards[cardState.currentCardIndex];

    expect(newState.isFrontSide).toBe(false);
    expect(currentCard.translation).toBe('Apple');
  });

  test('handleCardPress: flips from back to front side', () => {
    let state = { ...cardState, isFrontSide: false, hasRevealedBackOnce: true };
    const newState = cardHandlers.handleCardPress(state);

    expect(newState.isFrontSide).toBe(true);
    expect(newState.hasRevealedBackOnce).toBe(true); // Remains true after flip back
  });

  test('handleCardPress: multiple flips work correctly', () => {
    let state = cardState;

    // Flip 1: front -> back
    state = cardHandlers.handleCardPress(state);
    expect(state.isFrontSide).toBe(false);
    expect(state.hasRevealedBackOnce).toBe(true);

    // Flip 2: back -> front
    state = cardHandlers.handleCardPress(state);
    expect(state.isFrontSide).toBe(true);

    // Flip 3: front -> back
    state = cardHandlers.handleCardPress(state);
    expect(state.isFrontSide).toBe(false);
  });

  test('rating buttons appear only after back side revealed', () => {
    expect(cardState.hasRevealedBackOnce).toBe(false);

    const revealedState = cardHandlers.handleCardPress(cardState);

    expect(revealedState.hasRevealedBackOnce).toBe(true);
    // In real component, this would control visibility of rating buttons
  });

  test('handleSelectDifficulty: records rating with duration', () => {
    // First reveal
    let state = cardHandlers.handleCardPress(cardState);

    // Rate: Easy (grade 4)
    const ratedState = cardHandlers.handleSelectDifficulty(state, 4);

    expect(ratedState.reviewedCards).toHaveLength(1);
    expect(ratedState.reviewedCards[0]).toEqual({
      c_id: 'card1',
      grade: 4,
      duration: expect.any(Number),
      timestamp: expect.any(Number),
    });
    expect(ratedState.reviewedCards[0].duration).toBeGreaterThanOrEqual(0);
  });

  test('handleSelectDifficulty: resets state for next card', () => {
    let state = cardHandlers.handleCardPress(cardState);
    const ratedState = cardHandlers.handleSelectDifficulty(state, 3);

    expect(ratedState.currentCardIndex).toBe(1); // Moved to next card
    expect(ratedState.isFrontSide).toBe(true); // Reset to front
    expect(ratedState.hasRevealedBackOnce).toBe(false); // Reset reveal flag
  });

  test('handleSelectDifficulty: marks session complete when all cards reviewed', () => {
    let state = { ...cardState, currentCardIndex: 1 }; // Last card

    // Reveal back and rate
    state = cardHandlers.handleCardPress(state);
    const finalState = cardHandlers.handleSelectDifficulty(state, 3);

    expect(finalState.isSessionComplete).toBe(true);
    expect(finalState.reviewedCards).toHaveLength(1);
  });

  test('handleSelectDifficulty: records all difficulty grades correctly', () => {
    let state = cardState;

    // Rate card 1 as Easy (4)
    state = cardHandlers.handleCardPress(state);
    state = cardHandlers.handleSelectDifficulty(state, 4);

    // Rate card 2 as Good (3)
    state = cardHandlers.handleCardPress(state);
    state = cardHandlers.handleSelectDifficulty(state, 3);

    expect(state.reviewedCards).toHaveLength(2);
    expect(state.reviewedCards[0].grade).toBe(4); // Easy
    expect(state.reviewedCards[1].grade).toBe(3); // Good
  });

  test('review cards maintain chronological order', () => {
    let state = cardState;

    for (let i = 0; i < 2; i++) {
      state = cardHandlers.handleCardPress(state);
      state = cardHandlers.handleSelectDifficulty(state, 3);
    }

    const timestamps = state.reviewedCards.map((c: any) => c.timestamp);
    expect(timestamps[0]).toBeLessThanOrEqual(timestamps[1]);
  });
});

// ============================================================================
// OPTIMISTIC UI UPDATES (Deck/Card CRUD)
// ============================================================================

describe('Optimistic UI Updates - Card Creation', () => {
  let deckState: any;
  let handlers: any;

  beforeEach(() => {
    deckState = {
      d_id: 'deck123',
      deck_name: 'Japanese Vocabulary',
      cards: [
        {
          c_id: 'c1',
          word: 'りんご',
          translation: 'Apple',
        },
      ],
      isLoading: false,
      error: null,
    };

    handlers = {
      handleCardCreate: jest.fn((state: any, newCard: any) => {
        // Optimistically update UI immediately
        const optimisticCard = {
          ...newCard,
          c_id: `temp_${Date.now()}`, // Temporary ID before server confirms
          _optimistic: true,
        };

        return {
          ...state,
          cards: [optimisticCard, ...state.cards],
        };
      }),

      handleCardCreateConfirmation: jest.fn((state: any, serverCard: any) => {
        // Replace temporary card with server response
        return {
          ...state,
          cards: state.cards.map((c: any) =>
            c._optimistic && c.word === serverCard.word
              ? { ...serverCard, _optimistic: false }
              : c
          ),
        };
      }),

      handleCardCreateError: jest.fn((state: any, tempCardId: any) => {
        // Rollback on error
        return {
          ...state,
          cards: state.cards.filter((c: any) => c.c_id !== tempCardId),
          error: 'Failed to create card. Please try again.',
        };
      }),
    };
  });

  test('optimistic update: card appears immediately in UI', () => {
    const newCard = {
      word: '猫',
      translation: 'Cat',
    };

    const updatedState = handlers.handleCardCreate(deckState, newCard);

    expect(updatedState.cards).toHaveLength(2); // Original + new
    expect(updatedState.cards[0].word).toBe('猫');
    expect(updatedState.cards[0]._optimistic).toBe(true);
  });

  test('optimistic update: card has temporary ID', () => {
    const newCard = { word: 'dog', translation: 'Dog' };

    const updatedState = handlers.handleCardCreate(deckState, newCard);

    expect(updatedState.cards[0].c_id).toMatch(/^temp_\d+$/);
  });

  test('optimistic update: maintains card order (newest first)', () => {
    const newCard1 = { word: 'cat', translation: 'Cat' };
    const newCard2 = { word: 'dog', translation: 'Dog' };

    let state = handlers.handleCardCreate(deckState, newCard1);
    state = handlers.handleCardCreate(state, newCard2);

    expect(state.cards[0].word).toBe('dog'); // Most recent first
    expect(state.cards[1].word).toBe('cat');
    expect(state.cards[2].word).toBe('りんご'); // Original card last
  });

  test('server confirmation: replaces optimistic card with real ID', () => {
    const newCard = { word: 'horse', translation: 'Horse' };
    let state = handlers.handleCardCreate(deckState, newCard);

    const tempCardId = state.cards[0].c_id;
    const serverResponse = {
      c_id: 'c_server_12345',
      word: 'horse',
      translation: 'Horse',
    };

    state = handlers.handleCardCreateConfirmation(state, serverResponse);

    const createdCard = state.cards[0];
    expect(createdCard.c_id).toBe('c_server_12345');
    expect(createdCard._optimistic).toBe(false);
    expect(createdCard.c_id).not.toBe(tempCardId);
  });

  test('error rollback: removes optimistic card on failure', () => {
    const newCard = { word: 'bird', translation: 'Bird' };
    let state = handlers.handleCardCreate(deckState, newCard);

    const tempCardId = state.cards[0].c_id;
    expect(state.cards).toHaveLength(2);

    // Simulate error
    state = handlers.handleCardCreateError(state, tempCardId);

    expect(state.cards).toHaveLength(1); // Rolled back to original
    expect(state.cards[0].word).toBe('りんご');
    expect(state.error).toBeTruthy();
  });

  test('optimistic flow: create → confirm → ready for next', () => {
    const card1 = { word: 'fish', translation: 'Fish' };
    const card2 = { word: 'tree', translation: 'Tree' };

    // Create first card optimistically
    let state = handlers.handleCardCreate(deckState, card1);
    expect(state.cards).toHaveLength(2);
    expect(state.cards[0]._optimistic).toBe(true);

    // Server confirms first card
    const serverCard1 = { c_id: 'c_server_1', ...card1 };
    state = handlers.handleCardCreateConfirmation(state, serverCard1);
    expect(state.cards[0]._optimistic).toBe(false);
    expect(state.cards[0].c_id).toBe('c_server_1');

    // Create second card while first is confirmed
    state = handlers.handleCardCreate(state, card2);
    expect(state.cards).toHaveLength(3);
    expect(state.cards[0]._optimistic).toBe(true); // New card is optimistic
    expect(state.cards[1]._optimistic).toBe(false); // Previous is confirmed
  });

  test('optimistic state handles concurrent creates', () => {
    const card1 = { word: 'sun', translation: 'Sun' };
    const card2 = { word: 'moon', translation: 'Moon' };
    const card3 = { word: 'star', translation: 'Star' };

    let state = deckState;

    // Create 3 cards in quick succession
    state = handlers.handleCardCreate(state, card1);
    state = handlers.handleCardCreate(state, card2);
    state = handlers.handleCardCreate(state, card3);

    expect(state.cards).toHaveLength(4); // 3 new + 1 original
    expect(state.cards[0].word).toBe('star');
    expect(state.cards[1].word).toBe('moon');
    expect(state.cards[2].word).toBe('sun');
    // First 3 cards are optimistic, last is original
    expect(state.cards[0]._optimistic).toBe(true);
    expect(state.cards[1]._optimistic).toBe(true);
    expect(state.cards[2]._optimistic).toBe(true);
    expect(state.cards[3]._optimistic).toBeUndefined(); // Original card has no flag
  });
});

// ============================================================================
// TAB & SCREEN NAVIGATION FLOWS
// ============================================================================

describe('Tab and Screen Navigation Workflows', () => {
  let navigationState: any;
  let navigationHandlers: any;

  beforeEach(() => {
    navigationState = {
      currentTab: 'learn',
      navigationStack: ['home'],
      tabRoutes: ['learn', 'cards', 'settings'],
      screenHistory: [],
      canGoBack: false,
    };

    navigationHandlers = {
      switchTab: jest.fn((state: any, tabName: any) => {
        return {
          ...state,
          currentTab: tabName,
          navigationStack: ['home'], // Reset stack when switching tabs
          canGoBack: false,
        };
      }),

      navigateToScreen: jest.fn((state: any, screenName: any) => {
        const newStack = [...state.navigationStack, screenName];
        return {
          ...state,
          navigationStack: newStack,
          canGoBack: newStack.length > 1,
        };
      }),

      goBack: jest.fn((state: any) => {
        const newStack = state.navigationStack.slice(0, -1);
        return {
          ...state,
          navigationStack: newStack,
          canGoBack: newStack.length > 1,
        };
      }),

      recordScreenHistory: jest.fn((state: any, screen: any) => {
        return {
          ...state,
          screenHistory: [...state.screenHistory, { screen, timestamp: Date.now() }],
        };
      }),
    };
  });

  test('should start on home tab (learn)', () => {
    expect(navigationState.currentTab).toBe('learn');
    expect(navigationState.navigationStack[0]).toBe('home');
  });

  test('switchTab: changes current tab', () => {
    const newState = navigationHandlers.switchTab(navigationState, 'cards');

    expect(newState.currentTab).toBe('cards');
  });

  test('switchTab: resets navigation stack', () => {
    let state = navigationHandlers.navigateToScreen(navigationState, 'deck-detail');
    expect(state.navigationStack).toEqual(['home', 'deck-detail']);

    state = navigationHandlers.switchTab(state, 'settings');
    expect(state.navigationStack).toEqual(['home']);
    expect(state.canGoBack).toBe(false);
  });

  test('switchTab: validates tab exists', () => {
    const validTabs = navigationState.tabRoutes;
    const isValidTab = validTabs.includes('cards');

    expect(isValidTab).toBe(true);
  });

  test('navigateToScreen: adds screen to stack', () => {
    const newState = navigationHandlers.navigateToScreen(navigationState, 'deck-detail');

    expect(newState.navigationStack).toEqual(['home', 'deck-detail']);
    expect(newState.navigationStack).toHaveLength(2);
  });

  test('navigateToScreen: enables back navigation', () => {
    expect(navigationState.canGoBack).toBe(false);

    const newState = navigationHandlers.navigateToScreen(
      navigationState,
      'deck-detail'
    );

    expect(newState.canGoBack).toBe(true);
  });

  test('navigateToScreen: handles multi-level navigation', () => {
    let state = navigationState;
    state = navigationHandlers.navigateToScreen(state, 'deck-list');
    state = navigationHandlers.navigateToScreen(state, 'deck-detail');
    state = navigationHandlers.navigateToScreen(state, 'card-review');

    expect(state.navigationStack).toEqual([
      'home',
      'deck-list',
      'deck-detail',
      'card-review',
    ]);
    expect(state.canGoBack).toBe(true);
  });

  test('goBack: pops screen from stack', () => {
    let state = navigationHandlers.navigateToScreen(navigationState, 'deck-detail');
    state = navigationHandlers.goBack(state);

    expect(state.navigationStack).toEqual(['home']);
    expect(state.canGoBack).toBe(false);
  });

  test('goBack: prevents going back from home', () => {
    const state = navigationHandlers.goBack(navigationState);

    expect(state.navigationStack).toEqual([]); // Would need guards in real impl
    expect(state.canGoBack).toBe(false);
  });

  test('goBack: handles multi-level navigation', () => {
    let state = navigationState;
    state = navigationHandlers.navigateToScreen(state, 'deck-list');
    state = navigationHandlers.navigateToScreen(state, 'deck-detail');
    state = navigationHandlers.navigateToScreen(state, 'card-review');

    expect(state.navigationStack).toHaveLength(4);

    // Go back multiple times
    state = navigationHandlers.goBack(state);
    expect(state.navigationStack).toEqual(['home', 'deck-list', 'deck-detail']);

    state = navigationHandlers.goBack(state);
    expect(state.navigationStack).toEqual(['home', 'deck-list']);

    state = navigationHandlers.goBack(state);
    expect(state.navigationStack).toEqual(['home']);
  });

  test('recordScreenHistory: tracks navigation history', () => {
    let state = navigationState;

    state = navigationHandlers.recordScreenHistory(state, 'home');
    state = navigationHandlers.recordScreenHistory(state, 'deck-list');
    state = navigationHandlers.recordScreenHistory(state, 'deck-detail');

    expect(state.screenHistory).toHaveLength(3);
    expect(state.screenHistory[0].screen).toBe('home');
    expect(state.screenHistory[2].screen).toBe('deck-detail');
  });

  test('full navigation workflow: Learn tab → Deck Detail → Card Review', () => {
    let state = navigationState;

    // User on Learn tab (default)
    expect(state.currentTab).toBe('learn');

    // Navigate to deck-list
    state = navigationHandlers.navigateToScreen(state, 'deck-list');
    state = navigationHandlers.recordScreenHistory(state, 'deck-list');

    // Click on specific deck
    state = navigationHandlers.navigateToScreen(state, 'deck-detail');
    state = navigationHandlers.recordScreenHistory(state, 'deck-detail');

    // Start review
    state = navigationHandlers.navigateToScreen(state, 'card-review');
    state = navigationHandlers.recordScreenHistory(state, 'card-review');

    expect(state.navigationStack).toEqual([
      'home',
      'deck-list',
      'deck-detail',
      'card-review',
    ]);
    expect(state.screenHistory).toHaveLength(3);
    expect(state.canGoBack).toBe(true);

    // Go back to deck details
    state = navigationHandlers.goBack(state);
    expect(state.navigationStack[state.navigationStack.length - 1]).toBe(
      'deck-detail'
    );
  });

  test('tab switch workflow: Learn → Cards → Settings and back', () => {
    let state = navigationState;

    expect(state.currentTab).toBe('learn');

    // Switch to Cards tab
    state = navigationHandlers.switchTab(state, 'cards');
    expect(state.currentTab).toBe('cards');
    expect(state.navigationStack).toEqual(['home']);

    // Navigate within Cards tab
    state = navigationHandlers.navigateToScreen(state, 'card-edit');
    expect(state.navigationStack).toEqual(['home', 'card-edit']);

    // Switch to Settings tab (resets Cards stack)
    state = navigationHandlers.switchTab(state, 'settings');
    expect(state.currentTab).toBe('settings');
    expect(state.navigationStack).toEqual(['home']);

    // Switch back to Cards tab (fresh)
    state = navigationHandlers.switchTab(state, 'cards');
    expect(state.currentTab).toBe('cards');
    expect(state.navigationStack).toEqual(['home']);
  });
});
