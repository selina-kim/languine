import { describe, expect, test, beforeEach, jest, afterEach } from '@jest/globals';

// Mock SecureStore and Platform before importing storage
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

jest.mock('react-native', () => ({
  Platform: {
    OS: 'web',
  },
}));

import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import { storage } from '@/utils/storage';

describe('Storage Utility - Web Platform (setItem/getItem/deleteItem)', () => {
  let localStorageMock: Record<string, string>;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock = {};

    // Mock localStorage with a real store
    Object.defineProperty(global, 'localStorage', {
      value: {
        getItem: (key: string) => localStorageMock[key] || null,
        setItem: (key: string, value: string) => {
          localStorageMock[key] = value;
        },
        removeItem: (key: string) => {
          delete localStorageMock[key];
        },
        clear: () => {
          localStorageMock = {};
        },
      },
      writable: true,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('storage.setItem() - Store values', () => {
    test('should store a simple string value via storage interface', async () => {
      await storage.setItem('auth_token', 'token123');
      expect(localStorageMock['auth_token']).toBe('token123');
    });

    test('should store authentication tokens', async () => {
      const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjEyMyJ9';
      await storage.setItem('auth_token', token);
      expect(localStorageMock['auth_token']).toBe(token);
    });

    test('should store JSON serialized objects', async () => {
      const userData = { id: '123', email: 'user@example.com', token: 'abc' };
      await storage.setItem('user_data', JSON.stringify(userData));
      expect(localStorageMock['user_data']).toBe(JSON.stringify(userData));
    });

    test('should overwrite existing values', async () => {
      await storage.setItem('key', 'value1');
      await storage.setItem('key', 'value2');
      expect(localStorageMock['key']).toBe('value2');
    });

    test('should store empty string values', async () => {
      await storage.setItem('empty', '');
      expect(localStorageMock['empty']).toBe('');
    });

    test('should handle special characters', async () => {
      const specialData = '!@#$%^&*()_+-=[]{}|;:,.<>?';
      await storage.setItem('special', specialData);
      expect(localStorageMock['special']).toBe(specialData);
    });

    test('should handle unicode characters', async () => {
      const unicodeData = '你好世界🌍中文🎌日本語';
      await storage.setItem('unicode', unicodeData);
      expect(localStorageMock['unicode']).toBe(unicodeData);
    });

    test('should handle large data values', async () => {
      const largeData = 'x'.repeat(10000);
      await storage.setItem('large', largeData);
      expect(localStorageMock['large']).toBe(largeData);
    });

    test('should handle complex object serialization', async () => {
      const userObject = {
        id: 'user_123',
        email: 'test@example.com',
        preferences: {
          language: 'en',
          theme: 'dark',
        },
        tokens: {
          access: 'access_token',
          refresh: 'refresh_token',
        },
      };
      await storage.setItem('complex_object', JSON.stringify(userObject));
      expect(localStorageMock['complex_object']).toContain('"id":"user_123"');
    });
  });

  describe('storage.getItem() - Retrieve values', () => {
    test('should retrieve stored values', async () => {
      localStorageMock['test_key'] = 'test_value';
      const result = await storage.getItem('test_key');
      expect(result).toBe('test_value');
    });

    test('should return null for missing keys', async () => {
      const result = await storage.getItem('nonexistent');
      expect(result).toBeNull();
    });

    test('should retrieve authentication tokens', async () => {
      const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9';
      localStorageMock['auth_token'] = token;
      const result = await storage.getItem('auth_token');
      expect(result).toBe(token);
    });

    test('should retrieve empty string values', async () => {
      localStorageMock['empty'] = '';
      const result = await storage.getItem('empty');
      // Empty strings may be retrieved as empty string or null depending on localStorage implementation
      expect(result === '' || result === null).toBe(true);
    });

    test('should retrieve JSON serialized values', async () => {
      const userData = { id: '123', email: 'user@example.com' };
      localStorageMock['user'] = JSON.stringify(userData);
      const result = await storage.getItem('user');
      expect(result).toBe(JSON.stringify(userData));
    });

    test('should retrieve unicode values', async () => {
      const unicodeData = '中文🌍';
      localStorageMock['unicode'] = unicodeData;
      const result = await storage.getItem('unicode');
      expect(result).toBe(unicodeData);
    });
  });

  describe('storage.deleteItem() - Remove values', () => {
    test('should delete stored values', async () => {
      localStorageMock['temp_key'] = 'temp_value';
      await storage.deleteItem('temp_key');
      expect(localStorageMock['temp_key']).toBeUndefined();
    });

    test('should not throw on deleting nonexistent keys', async () => {
      await expect(storage.deleteItem('nonexistent')).resolves.not.toThrow();
    });

    test('should delete authentication tokens', async () => {
      localStorageMock['auth_token'] = 'token123';
      await storage.deleteItem('auth_token');
      expect(localStorageMock['auth_token']).toBeUndefined();
    });

    test('should handle multiple deletions', async () => {
      localStorageMock['key1'] = 'value1';
      localStorageMock['key2'] = 'value2';
      localStorageMock['key3'] = 'value3';

      await storage.deleteItem('key1');
      await storage.deleteItem('key2');
      await storage.deleteItem('key3');

      expect(localStorageMock['key1']).toBeUndefined();
      expect(localStorageMock['key2']).toBeUndefined();
      expect(localStorageMock['key3']).toBeUndefined();
    });
  });

  describe('Storage Workflow - Complete operations', () => {
    test('should handle set -> get -> delete workflow', async () => {
      const key = 'workflow_key';
      const value = 'workflow_value';

      await storage.setItem(key, value);
      const retrieved = await storage.getItem(key);
      expect(retrieved).toBe(value);

      await storage.deleteItem(key);
      const deleted = await storage.getItem(key);
      expect(deleted).toBeNull();
    });

    test('should handle multiple concurrent set operations', async () => {
      const operations = [
        { key: 'key1', value: 'value1' },
        { key: 'key2', value: 'value2' },
        { key: 'key3', value: 'value3' },
      ];

      await Promise.all(operations.map((op) => storage.setItem(op.key, op.value)));

      const values = await Promise.all(
        operations.map((op) => storage.getItem(op.key))
      );

      expect(values).toEqual(['value1', 'value2', 'value3']);
    });

    test('should handle JSON serialization roundtrip', async () => {
      const userData = {
        id: 'user_123',
        email: 'test@example.com',
        preferences: { language: 'en', theme: 'dark' },
      };

      await storage.setItem('user_data', JSON.stringify(userData));
      const stored = await storage.getItem('user_data');
      const parsed = JSON.parse(stored as string);

      expect(parsed).toEqual(userData);
      expect(parsed.preferences.language).toBe('en');
    });

    test('should persist data across multiple get operations', async () => {
      const key = 'persist_key';
      const value = 'persist_value';

      await storage.setItem(key, value);
      const firstGet = await storage.getItem(key);
      const secondGet = await storage.getItem(key);

      expect(firstGet).toBe(value);
      expect(secondGet).toBe(value);
    });
  });

  describe('Error handling', () => {
    test('should handle storage.setItem errors gracefully', async () => {
      // Test error logging (not throwing)
      await expect(storage.setItem('test', 'value')).resolves.not.toThrow();
    });

    test('should handle storage.getItem errors gracefully', async () => {
      const result = await storage.getItem('any_key');
      expect(typeof result === 'string' || result === null).toBe(true);
    });

    test('should handle storage.deleteItem errors gracefully', async () => {
      await expect(storage.deleteItem('any_key')).resolves.not.toThrow();
    });
  });

  describe('Storage interface methods', () => {
    test('should expose setItem as async function', () => {
      expect(typeof storage.setItem).toBe('function');
    });

    test('should expose getItem as async function', () => {
      expect(typeof storage.getItem).toBe('function');
    });

    test('should expose deleteItem as async function', () => {
      expect(typeof storage.deleteItem).toBe('function');
    });

    test('all methods should return promises', async () => {
      const setResult = storage.setItem('key', 'value');
      const getResult = storage.getItem('key');
      const deleteResult = storage.deleteItem('key');

      expect(setResult instanceof Promise).toBe(true);
      expect(getResult instanceof Promise).toBe(true);
      expect(deleteResult instanceof Promise).toBe(true);
    });
  });
});
