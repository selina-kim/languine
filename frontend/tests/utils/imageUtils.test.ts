import { describe, expect, test, beforeEach } from '@jest/globals';
import { getImageUrl, isBackendImageUrl } from '@/utils/imageUtils';

// Mock environment variables
const originalEnv = process.env;

describe('Image Utils - getImageUrl', () => {
  beforeEach(() => {
    process.env = { ...originalEnv };
    process.env.EXPO_PUBLIC_API_URL = 'https://api.example.com';
  });

  test('should return null for null object ID', () => {
    const result = getImageUrl(null);
    expect(result).toBeNull();
  });

  test('should return null for empty string', () => {
    const result = getImageUrl('');
    expect(result).toBeNull();
  });

  test('should construct backend image URL from object ID', () => {
    const objectId = 'images/card_13.jpg';
    const result = getImageUrl(objectId);

    expect(result).toContain('/cards/image/');
    expect(result).toContain('images');
  });

  test('should return full backend URLs unchanged', () => {
    const url = 'https://api.example.com/cards/image/card_123';
    const result = getImageUrl(url);

    expect(result).toBe(url);
  });

  test('should return external absolute URLs unchanged', () => {
    const unsplashUrl = 'https://images.unsplash.com/photo-123.jpg';
    const result = getImageUrl(unsplashUrl);

    expect(result).toBe(unsplashUrl);
  });

  test('should handle URL-encoded absolute URLs', () => {
    const encoded = 'https:%2F%2Fimages.unsplash.com%2Fphoto.jpg';
    const result = getImageUrl(encoded);

    expect(result).toBe('https://images.unsplash.com/photo.jpg');
  });

  test('should encode special characters in object ID', () => {
    const objectId = 'images/card with spaces.jpg';
    const result = getImageUrl(objectId);

    expect(result).toContain('%20');
  });

  test('should return object ID when API URL not configured', () => {
    delete process.env.EXPO_PUBLIC_API_URL;
    const objectId = 'images/card_13.jpg';
    const result = getImageUrl(objectId);

    expect(result).toBe(objectId);
  });
});

describe('Image Utils - isBackendImageUrl', () => {
  beforeEach(() => {
    process.env = { ...originalEnv };
    process.env.EXPO_PUBLIC_API_URL = 'https://api.example.com';
  });

  test('should identify backend URLs correctly', () => {
    const backendUrl = 'https://api.example.com/cards/image/image123';
    const result = isBackendImageUrl(backendUrl);

    expect(result).toBe(true);
  });

  test('should reject external URLs', () => {
    const externalUrl = 'https://images.unsplash.com/photo.jpg';
    const result = isBackendImageUrl(externalUrl);

    expect(result).toBe(false);
  });

  test('should handle missing API URL', () => {
    delete process.env.EXPO_PUBLIC_API_URL;
    const url = 'https://api.example.com/cards/image/image123';
    const result = isBackendImageUrl(url);

    expect(result).toBe(false);
  });
});
