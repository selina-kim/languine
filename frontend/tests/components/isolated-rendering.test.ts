import { describe, expect, test, jest } from '@jest/globals';

// Mock external dependencies FIRST before any imports
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
// COMPONENT IMPORTS - Verify all exports exist
// ============================================================================

describe('Common Components - Exports', () => {
  test('should import CText component', () => {
    const CText = require('@/components/common/CText').CText;
    expect(typeof CText).toBe('function');
  });

  test('should import CButton component', () => {
    const CButton = require('@/components/common/CButton').CButton;
    expect(typeof CButton).toBe('function');
  });

  test('should import CTextInput component', () => {
    const CTextInput = require('@/components/common/CTextInput').CTextInput;
    expect(typeof CTextInput).toBe('function');
  });

  test('should import CSwitch component', () => {
    const CSwitch = require('@/components/common/CSwitch').CSwitch;
    expect(typeof CSwitch).toBe('function');
  });

  test('should import Modal component', () => {
    const Modal = require('@/components/common/Modal').Modal;
    expect(typeof Modal).toBe('function');
  });

  test('should import RouteButton component', () => {
    const RouteButton = require('@/components/common/RouteButton').RouteButton;
    expect(typeof RouteButton).toBe('function');
  });

  test('should import Dropdown component', () => {
    const Dropdown = require('@/components/common/Dropdown').Dropdown;
    expect(typeof Dropdown).toBe('function');
  });
});

describe('Feature Components - Exports', () => {
  test('should export DeckPreview', () => {
    const DeckPreview = require('@/components/features/decks/DeckPreview').DeckPreview;
    expect(typeof DeckPreview).toBe('function');
  });

  test('should export NoDecksBanner', () => {
    const NoDecksBanner = require('@/components/features/decks/NoDecksBanner').NoDecksBanner;
    expect(typeof NoDecksBanner).toBe('function');
  });

  test('should export CreateNewDeckModal', () => {
    const CreateNewDeckModal = require('@/components/features/decks/CreateNewDeckModal')
      .CreateNewDeckModal;
    expect(typeof CreateNewDeckModal).toBe('function');
  });

  test('should import CreateNewCardModal component', () => {
    const CreateNewCardModal = require('@/components/features/decks/CreateNewCardModal')
      .CreateNewCardModal;
    expect(typeof CreateNewCardModal).toBe('function');
  });

  test('should import SingleDeckDetails component', () => {
    const SingleDeckDetails = require('@/components/features/decks/SingleDeckDetails')
      .SingleDeckDetails;
    expect(typeof SingleDeckDetails).toBe('function');
  });

  test('should import CardsList component', () => {
    const CardsList = require('@/components/features/decks/CardsList').CardsList;
    expect(typeof CardsList).toBe('function');
  });

  test('should import CardsDueBanner component', () => {
    const CardsDueBanner = require('@/components/features/index/CardsDueBanner').CardsDueBanner;
    expect(typeof CardsDueBanner).toBe('function');
  });

  test('should import LastReviewedDeckItem component', () => {
    const LastReviewedDeckItem = require('@/components/features/index/LastReviewedDeckItem')
      .LastReviewedDeckItem;
    expect(typeof LastReviewedDeckItem).toBe('function');
  });

  test('should import RevisionDeckPreview component', () => {
    const RevisionDeckPreview = require('@/components/features/revision/RevisionDeckPreview')
      .RevisionDeckPreview;
    expect(typeof RevisionDeckPreview).toBe('function');
  });

  test('should import SingleDeckReview component', () => {
    const SingleDeckReview = require('@/components/features/revision/SingleDeckReview')
      .SingleDeckReview;
    expect(typeof SingleDeckReview).toBe('function');
  });

  test('should import ProfileSettings component', () => {
    const ProfileSettings = require('@/components/features/settings/ProfileSettings')
      .ProfileSettings;
    expect(typeof ProfileSettings).toBe('function');
  });

  test('should import OptimizationSettings component', () => {
    const OptimizationSettings = require('@/components/features/settings/OptimizationSettings')
      .OptimizationSettings;
    expect(typeof OptimizationSettings).toBe('function');
  });

  test('should import AccountSettings component', () => {
    const AccountSettings = require('@/components/features/settings/AccountSettings')
      .AccountSettings;
    expect(typeof AccountSettings).toBe('function');
  });

  test('should import DeleteAccountButton component', () => {
    const DeleteAccountButton = require('@/components/features/settings/DeleteAccountButton')
      .DeleteAccountButton;
    expect(typeof DeleteAccountButton).toBe('function');
  });

  test('should import ResetParametersButton component', () => {
    const ResetParametersButton = require('@/components/features/settings/ResetParametersButton')
      .ResetParametersButton;
    expect(typeof ResetParametersButton).toBe('function');
  });

  test('should import InfoContainer component', () => {
    const InfoContainer = require('@/components/features/help/InfoContainer').InfoContainer;
    expect(typeof InfoContainer).toBe('function');
  });

  test('should import StepContainer component', () => {
    const StepContainer = require('@/components/features/help/StepContainer').StepContainer;
    expect(typeof StepContainer).toBe('function');
  });

  test('should import FAQ component', () => {
    const FAQ = require('@/components/features/help/FAQ').FAQ;
    expect(typeof FAQ).toBe('function');
  });

  test('should export TipsContainer', () => {
    const TipsContainer = require('@/components/features/help/TipsContainer').TipsContainer;
    expect(typeof TipsContainer).toBe('function');
  });
});

