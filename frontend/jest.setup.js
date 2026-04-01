// Simple mock setup for React Native testing
jest.mock('react-native', () => ({
  View: 'View',
  Text: 'Text',
  Pressable: 'Pressable',
  ScrollView: 'ScrollView',
  TextInput: 'TextInput',
  StyleSheet: {
    create: (styles) => styles,
  },
  Alert: {
    alert: jest.fn(),
  },
  Keyboard: {
    dismiss: jest.fn(),
  },
  Platform: {
    select: (obj) => obj.default,
    OS: 'ios',
  },
}));

// Mock common icons and components
jest.mock('@/assets/icons/DecksIcon', () => ({
  DecksIcon: () => null,
}));

jest.mock('@/assets/icons/PlusIcon', () => ({
  PlusIcon: () => null,
}));

jest.mock('@/assets/icons/TrashIcon', () => ({
  TrashIcon: () => null,
}));

jest.mock('@/assets/icons/EditIcon', () => ({
  EditIcon: () => null,
}));

jest.mock('@/assets/icons/PlayIcon', () => ({
  PlayIcon: () => null,
}));

jest.mock('@/assets/icons/HomeIcon', () => ({
  HomeIcon: () => null,
}));

jest.mock('@/assets/icons/HelpIcon', () => ({
  HelpIcon: () => null,
}));

jest.mock('@/assets/icons/ProfileIcon', () => ({
  ProfileIcon: () => null,
}));

jest.mock('@/assets/icons/PlusFilledIcon', () => ({
  PlusFilledIcon: () => null,
}));

jest.mock('@/assets/icons/ChevronDownIcon', () => ({
  ChevronDownIcon: () => null,
}));

jest.mock('@/assets/icons/OpenBookIcon', () => ({
  OpenBookIcon: () => null,
}));

jest.mock('@/assets/icons/RepeatIcon', () => ({
  RepeatIcon: () => null,
}));

jest.mock('@/assets/icons/SoundIcon', () => ({
  SoundIcon: () => null,
}));

jest.mock('@/assets/icons/MagicWandIcon', () => ({
  MagicWandIcon: () => null,
}));

// Mock Expo modules
jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    back: jest.fn(),
    replace: jest.fn(),
  }),
  useLocalSearchParams: () => ({}),
}));

jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: jest.fn(),
    goBack: jest.fn(),
    push: jest.fn(),
  }),
  useRoute: () => ({
    params: {},
  }),
}));

// Suppress console warnings
const originalWarn = console.warn;
beforeAll(() => {
  console.warn = jest.fn((...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Non-serializable values')
    ) {
      return;
    }
    originalWarn(...args);
  });
});

afterAll(() => {
  console.warn = originalWarn;
});
